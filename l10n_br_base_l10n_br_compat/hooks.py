# Copyright (C) 2025 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
import unicodedata

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    _merge_l10n_br_cities(env)


def _normalize_name(name):
    if not name:
        return ""
    return "".join(
        c
        for c in unicodedata.normalize("NFKD", name.lower())
        if not unicodedata.combining(c)
    ).strip()


def _build_oca_city_map(env):
    # We use a normalized key: (state_id, normalized_name)
    # We prioritize cities that have an IBGE code (OCA cities)
    oca_cities = (
        env["res.city"]
        .with_context(active_test=False)
        .search([("state_id", "!=", False)])
    )
    oca_city_map = {}
    for city in oca_cities:
        key = (city.state_id.id, _normalize_name(city.name))
        # In l10n_br_base, the field is 'ibge_code'
        has_ibge = hasattr(city, "ibge_code") and city.ibge_code
        if key not in oca_city_map or has_ibge:
            oca_city_map[key] = city
    return oca_city_map


def _redirect_and_collect_duplicates(env, city_data, oca_city_map):
    to_delete = env["res.city"]
    merged_count = 0

    for data in city_data:
        core_city = env["res.city"].with_context(active_test=False).browse(data.res_id)
        if not core_city.exists():
            continue

        key = (core_city.state_id.id, _normalize_name(core_city.name))
        oca_city = oca_city_map.get(key)

        if oca_city and oca_city.id != core_city.id:
            # Update the external ID to point to the OCA city
            data.write({"res_id": oca_city.id})
            # Prepare to delete the duplicate core city
            if core_city not in to_delete:
                to_delete |= core_city
            merged_count += 1
    return to_delete, merged_count


def _update_references(env, to_delete, oca_city_map):
    # Update references in l10n_br.zip.range before deleting
    zip_ranges = (
        env["l10n_br.zip.range"]
        .with_context(active_test=False)
        .search([("city_id", "in", to_delete.ids)])
    )
    if zip_ranges:
        _logger.info("Updating city_id for %d zip ranges", len(zip_ranges))
        for zip_range in zip_ranges:
            key = (
                zip_range.city_id.state_id.id,
                _normalize_name(zip_range.city_id.name),
            )
            oca_city = oca_city_map.get(key)
            if oca_city:
                zip_range.write({"city_id": oca_city.id})

    # Update references in res.partner before deleting
    partners = (
        env["res.partner"]
        .with_context(active_test=False)
        .search([("city_id", "in", to_delete.ids)])
    )
    if partners:
        _logger.info("Updating city_id for %d partners", len(partners))
        for partner in partners:
            key = (partner.city_id.state_id.id, _normalize_name(partner.city_id.name))
            oca_city = oca_city_map.get(key)
            if oca_city:
                partner.write({"city_id": oca_city.id})


def _delete_cities(env, to_delete):
    _logger.info("Unlinking cities in batch...")
    try:
        to_delete.unlink()
    except Exception as e:
        _logger.warning(
            "Batch unlink failed, falling back to individual unlink. Error: %s", e
        )
        for city in to_delete:
            try:
                with env.cr.savepoint():
                    city.unlink()
            except Exception:
                _logger.warning(
                    "Could not delete duplicate city %s (ID %s)", city.name, city.id
                )


def _merge_l10n_br_cities(env):
    _logger.info("Merging l10n_br cities into l10n_br_base cities...")

    city_data = env["ir.model.data"].search(
        [("module", "=", "l10n_br"), ("model", "=", "res.city")]
    )

    if not city_data:
        _logger.info("No cities from l10n_br found to merge.")
        return

    oca_city_map = _build_oca_city_map(env)
    to_delete, merged_count = _redirect_and_collect_duplicates(
        env, city_data, oca_city_map
    )

    if to_delete:
        _logger.info("Deleting %d duplicate cities from l10n_br", len(to_delete))
        _update_references(env, to_delete, oca_city_map)
        _delete_cities(env, to_delete)

    _logger.info("Successfully merged %d cities.", merged_count)
