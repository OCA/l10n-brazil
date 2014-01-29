# -*- coding: utf-8 -*-
from datetime import datetime, date
from lxml import etree
import time
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.addons.base_status.base_stage import base_stage
from openerp.addons.resource.faces import task as Task


################ PRODUCT BACKLOG #######################
class scrum_product_backlog(osv.osv):
	_name = "scrum.product.backlog"
	_description = "Product Backlog"
	_columns = {
		'name': fields.char('Name',size=155,required=True),
		'releases': fields.one2many('scrum.release.backlog','product_backlog_id','Releases',readonly=True),
		'items': fields.one2many('scrum.product.backlog.item','product_backlog_id','Items',ondelete='cascade'),
		'product_owner': fields.many2one('res.users','Product Owner',required=True),
		'scrum_master': fields.many2one('res.users','Scrum Master',required=True),
		'project_id': fields.many2one('project.project','Project'),
		'project_progress_rate': fields.related('project_id', 'progress_rate', string='Progress', readonly=True),
	}

	def create(self,cr,uid,vals,context=None):
		b = super(scrum_product_backlog, self).create(cr, uid, vals, context=context)
		project = self.pool.get('project.project').write(cr,uid,vals['project_id'],{'product_backlog_id':b})
		return b
	
################ RELEASE BACKLOG #######################
class scrum_release_backlog(osv.osv):
	_name = "scrum.release.backlog"
	_description = "Release Backlog"
	_columns = {
		'name': fields.char('Name',size=155,required=True),
		'product_backlog_id': fields.many2one('scrum.product.backlog','Product Backlog'),
		'sprints': fields.one2many('scrum.sprint','release_backlog_id','Sprints',readonly=True),
		'items': fields.one2many('scrum.product.backlog.item','release_backlog_id','Items'),
	}

	_defaults = {
		'product_backlog_id': lambda self,cr,uid,c: c.get('product_backlog_id',False)
	}

################ SPRINT #######################
class scrum_sprint(osv.osv):
	_name = "scrum.sprint"
	_description = "Scrum Sprint"

	def _progress_rate(self, cr, uid, ids, names, arg, context=None):
		res = {}
		for s in self.browse(cr,uid,ids):
			ph = 0
			th = 0
			
			for i in s.items:
				ph += i.task.planned_hours
				th += i.task.total_hours
			h_remaining = (th - ph)
			res[s.id]['progress'] = h_remaining
			#raise osv.except_osv(_('Error !'), _("'%s'") % unicode(str(h_remaining)))


	_columns = {
		'name': fields.char('Name',size=155,required=True),
		'product_backlog_id': fields.many2one('scrum.product.backlog','Product Backlog',required=True),
		'release_backlog_id': fields.many2one('scrum.release.backlog','Release Backlog',required=True),
		'product_owner': fields.related('product_backlog_id','product_owner',type="many2one",relation="res.users",string='Product Owner',store=True,required=True),
		'scrum_master': fields.related('product_backlog_id','scrum_master',type="many2one",relation="res.users",string='Scrum Master',store=True,required=True),
		'days': fields.char('Days Duration',size=2,required=True,readonly=True),
		'start_date': fields.date('Start Date',required=True),
		'end_date': fields.date('End Date',required=True),
		'items': fields.one2many('scrum.product.backlog.item','sprint_id','Items'),
		'meetings': fields.one2many('scrum.meeting','sprint_id','Meetings'),
		#'progress_rate': fields.function(_progress_rate, multi="progress", string='Progress', type='float', group_operator="avg", help="Sprint progress."),
	}

	def get_pb_id(self,cr,uid,context):
		if 'product_backlog_id' in context:
			return context['product_backlog_id']
		else:
			return 0

	def get_rb_id(self,cr,uid,context):
		if 'release_backlog_id' in context:
			return context['release_backlog_id']
		else:
			return 0

	_defaults = {
		'product_backlog_id': get_pb_id,#lambda self, cr, uid, c: c.get('product_backlog_id', False),
		'release_backlog_id': get_rb_id,#lambda self, cr, uid, c: c.get('release_backlog_id', False),
	}

	def onchange_pb_id(self,cr,uid,ids,product_backlog,release_backlog_id,context=None):
		if product_backlog == False:
			return False

		pb = self.pool.get('scrum.product.backlog')
		pb_item = pb.browse(cr,uid,product_backlog)

		product_owner = pb_item.product_owner.id
		scrum_master = pb_item.scrum_master.id

		return {'value': {'product_owner': product_owner,'scrum_master':scrum_master}}

	def calculate_days(self,cr,uid,ids,start_date,end_date,context=None):
		#raise osv.except_osv(_('Error !'), _("'%s'") % unicode(str(start_date)))
		if start_date == False or end_date == False:
			return False

		date_format = "%Y-%m-%d"
		a = datetime.strptime(start_date, date_format)
		b = datetime.strptime(end_date, date_format)
		delta = b - a

		days = "%s dias" % (delta.days)

		return {'value':{'days':days}}


################ ITEM BACKLOG #######################
class scrum_product_backlog_item(osv.osv):
	_name = "scrum.product.backlog.item"
	_description = "Product Backlog Item"
	_columns = {
		'name': fields.char('Name',size=155,required=True),
		'priority': fields.selection([('4','Very Low'), ('3','Low'), ('2','Medium'), ('1','Important'), ('0','Very important')], 'Priority', select=True),
		'sequence': fields.integer('Sequence', select=True),
		'description': fields.text('Description',size=500),
		'task': fields.many2one('project.task','Task',readonly=True),
		'product_backlog_id': fields.many2one('scrum.product.backlog','Product Backlog',required=True),
		'release_backlog_id': fields.many2one('scrum.release.backlog','Release Backlog',required=True),
		'sprint_id': fields.many2one('scrum.sprint','Sprint',required=True),
		'requestor': fields.many2one('hr.employee','Requestor'),
		'task_progress': fields.related('task', 'progress', string='Progress', readonly=True),
		'task_user_id': fields.related('task', 'user_id', type="many2one",relation="res.users",string='Assigned to'),
		'ref': fields.many2one('scrum.product.backlog.item.ref','Reference'),
		'type': fields.selection((('bug','Bug'),('feature','Melhoria')),'Type'),
	}
	_defaults = {
	"product_backlog_id": lambda self, cr, uid, c: c.get('product_backlog_id', False),
	}

	def create(self,cr,uid,vals,context=None):


		pb = self.pool.get('scrum.product.backlog').browse(cr,uid,vals.get('product_backlog_id')).id
		rb = self.pool.get('scrum.product.backlog').browse(cr,uid,vals.get('release_backlog_id')).id
		s = self.pool.get('scrum.sprint').browse(cr,uid,vals.get('sprint_id')).id

		pj = self.pool.get('project.project')
		pj_search = pj.search(cr,uid,[('product_backlog_id','=',pb)])

		if not pj_search:
			raise osv.except_osv(_(u'Atenção!'), _("%s") % (u'O seu usuário não possui acesso no Projeto associado ao Product Backlog. Favor solicitar acesso!'))

		res = {'name':vals.get('name'),'project_id':pj_search[0],'release_backlog_id': rb,'sprint_id':s}

		task_item = self.pool.get('project.task')
		task = task_item.create(cr,uid,res,context=context)

		vals['task'] = task

		return super(scrum_product_backlog_item, self).create(cr, uid, vals, context=context)

	def unlink(self, cr, uid, ids, context=None, check=True):

		task_obj = self.pool.get('project.task')
		s = self.browse(cr,uid,ids,context=context)

		task_list = []
		for item in s:

			task_list.append(item.task.id)

		task_obj.unlink(cr, uid, task_list, context=context)

		return super(scrum_product_backlog_item, self).unlink(cr, uid, ids, context)

	def write(self, cr, user, ids, vals, context=None):



		res = {}
		if 'release_backlog_id' in vals:
			res.update({'release_backlog_id': vals['release_backlog_id']})

		if 'sprint_id' in vals:
			res.update({'sprint_id':vals['sprint_id']})

		

		s = self.browse(cr,user,ids)

		for item in s:
			if item.task.id:
				task = self.pool.get('project.task').write(cr,user,item.task.id,res,context=context)
			else:
				
				pj = self.pool.get('project.project')
				pj_search = pj.search(cr,user,[('product_backlog_id','=',item.product_backlog_id.id)])

				res = {'name':item.name,'project_id':pj_search[0],'release_backlog_id': item.release_backlog_id.id,'sprint_id':item.sprint_id.id}
				#raise osv.except_osv(_('Error !'), _("'%s'") % unicode(str(res)))
				task = self.pool.get('project.task').create(cr,user,res,context=context)


		return super(scrum_product_backlog_item, self).write(cr, user, ids, vals, context=context)

################ SCRUM MEETING #######################
class scrum_meeting(osv.osv):
	_name = "scrum.meeting"
	_description = "Scrum Meeting"
	_columns = {
		'date': fields.date('Date'),
		'last_work': fields.text('Last Works',size=500,help="What you performed since the last meeting?"),
		'next_work': fields.text('Next Works',size=500,help="What do you plan to hold the next meeting?"),
		'blocking': fields.text('Blocking',size=500,help="There is something blocking you?"),
		'sprint_id': fields.many2one('scrum.sprint','Sprint'),
	}
	_defaults = {
		'date': lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
	}


################ PROJECT #######################
class project(osv.osv):
	_inherit = "project.project"
	_columns = {
		'scrum_project': fields.boolean('Scrum Project'),
		'product_backlog_id': fields.many2one('scrum.product.backlog','Product Backlog',readonly=True),

	}


################ TASK #######################
class task(osv.osv):
	_inherit = "project.task"
	_columns = {
		'release_backlog_id': fields.many2one('scrum.release.backlog','Release Backlog',readonly=True),
		'sprint_id': fields.many2one('scrum.sprint','Sprint',readonly=True),
	}

class scrum_product_backlog_item_ref(osv.osv):
	_name = 'scrum.product.backlog.item.ref'
	_columns = {
		'name': fields.char('Name',size=155,required=True),
	}