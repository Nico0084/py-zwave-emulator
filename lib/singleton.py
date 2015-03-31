# -*- coding: utf-8 -*-
options = None

class Options:
 
    def __init__(self):
        global options
        options = self
    
    def __del__(self):
        global options
        options = self

class Manager(object):
    
#    class __Singleton:
#        
#        def __init__(self):
#            global options
#            print "In init"
#            if options is None :
#                print " fisrt call"
#                options = Options()
#            self.val = None
#         
#        def __str__(self):
#            return `self`  + "{0}".format(self.val)
#        
#        def __del__(self):
#            print "Détruit"
         
    instance = None
    
    def __new__(cls, *args, **kargs):
        print "In new"
        if options is not None :
            if  Manager.instance is None:
                print 'création'
                print options
                Manager.instance = object.__new__(cls, *args, **kargs)
            else : print 'copie',  options
        else : 
            print "no options set, quit"
            exit()
        return Manager.instance

    def __init__(self):
        print "In init manager"
    
    def __del__(self):
        print "Détruit"
        self.instance = None
    
    def __enter__(self):
        print "Enter manager"
        
    def close(self):
        print "Close manager"

    def __exit__(self, type, value, traceback):
        print "exit manager"
        
    def create(self):
        print "create manager"
            
o= Options()
a = Manager()
a.create()

b= Manager()
print a,  b
del(a)
print b
del(b)
try :
    if a: print "instance a exist"
except :
    print "no a instance"
try : 
    if b : print "b exist"
except :
    print "no b instance"   
b= Manager()
print b
print b.__dict__
