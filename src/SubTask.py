#!usr/bin/python
# -*- coding: utf-8 -*-import string

'''
A superclass to handle progress report of threaded tasks
'''

class SubTask():
	def __init__(self, taskname:str="", weight:int=1):
		self.taskname = taskname
		#self.current_computation_step = ""
		#self.current_computation_description = ""
		#self.current_computation_progress = 0
		self.children = []
		self.weight = weight
		self.progress = 0
		self.error = False
		self.outputfilepath = None

	def __str__(self) -> str:
		retstr = "task: "+self.taskname+" ("
		for c in self.children:
			retstr += str(c)+" "
		retstr += ")"
		return retstr

	def start_progress(self) -> None:
		self.progress = 0
		self.children.clear()

	def finish_progress(self) -> None:
		print ("Finish task:", self.taskname)
		print ("  (current progress:",self.progress,"/",self.weight,")")
		for c in self.children:
			c.finish_progress()
		self.progress = self.weight

	def add_task_child(self, child) -> None:
		self.children.append(child)

	def get_total_weight(self, verbose:bool=False) -> int:
		if verbose:
			print ("weight:",[self.weight]+[c.get_total_weight(False) for c in self.children])
		return self.weight+sum(c.get_total_weight(False) for c in self.children)

	def get_progress_sum(self, verbose:bool=False) -> int:
		if verbose:
			print ("progress:",[self.progress]+[c.get_progress_sum(False) for c in self.children])
		return self.progress+sum(c.get_progress_sum() for c in self.children)

	def get_progress_percentage(self) -> float:
		prg_sum = self.get_progress_sum()
		prg_weight = self.get_total_weight()
		print ("progress:",prg_sum,"/",prg_weight)
		return prg_sum/prg_weight

	#def get_progress(self):
	#	progress_sum = sum(c.get_progress() for c in self.children)+self.progress
	#	return progress_sum/self.get_total_weight()

	def get_current_taskname(self) -> str:
		taskname = None
		for c in self.children:
			child_taskname = c.get_current_taskname()
			if child_taskname is not None:
				taskname = child_taskname
		if taskname is None and self.progress < self.weight:
			taskname = self.taskname
		return taskname

	def get_progress_dict(self) -> dict:
		total_progress = self.get_progress_percentage()
		if self.error:
			status = "stopped"
		elif total_progress <= 0:
			status = "inactive"
		elif total_progress < 1:
			status = "active"
		elif total_progress >= 1:
			status = "finished"
		return {
			"current_task" : self.get_current_taskname(),
			"current_status" : status,
			"total_progress" : total_progress
		}
