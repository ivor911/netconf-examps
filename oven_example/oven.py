#!/usr/bin/env python3
from __future__ import print_function
import threading
import time
import sysrepo as sr
import sys
#import yang as ly

#Global oven variables

#oven yang config value stored locally just so that it is not needed to as sysrepo for it all the time.
#oven_power used to determining whether the power of oven is turned on(true) or off(false).
oven_power=0
#config_temperature used to determining whether the configure temperature of oven.
config_temperature=200

#oven state value determining whether the food is inside the oven or not 
#NOTE: we only start cooking when food_inside=1.
food_inside=0
#oven state value determining the current temperature of the oven.
oven_temperature=0
#oven state value determining whether the food is waiting for the oven to be ready 
insert_food_on_ready= 0

stop_oven_thread = 0
oven_thread_running = 0

def strTo1(x):
    x = int(x == 'true')
    return x

def oven_thread():
    global oven_power
    global config_temperature
    global food_inside
    global oven_temperature
    global insert_food_on_ready
    global stop_oven_thread
    global oven_thread_running
    
    thread_name = threading.current_thread().name
    while True: 
        oven_thread_running = 1
        time.sleep(1)
        if (oven_temperature < config_temperature):
            # oven is heating up 50 degrees per second until the set temperature 
            if (oven_temperature + 50 < config_temperature):
                oven_temperature += 50
            else:
                oven_temperature = config_temperature
                #oven reached the desired temperature, create a notification
                #TODO 
                #rc = sr_event_notif_send(sess, "/oven:oven-ready", NULL, 0);
                #if (rc != SR_ERR_OK):
                #    SRP_LOG_ERR("OVEN: Oven-ready notification generation failed: %s.", sr_strerror(rc));
                #}
            
        elif (oven_temperature > config_temperature):
            # oven is cooling down but it will never be colder than the room temperature 
            desired_temperature = 25 if config_temperature < 25 else config_temperature
            if (oven_temperature - 20 > desired_temperature):
                oven_temperature -= 20
            else:
                oven_temperature = desired_temperature

        print("[oven_thread({})] config_temperature is {} , oven_temperature is {} ".format(thread_name, config_temperature, oven_temperature))
        if (insert_food_on_ready and oven_temperature >= config_temperature):
            #food is inserted once the oven is ready 
            insert_food_on_ready = 0
            food_inside = 1
            print("[oven_thread({})] Food put into the oven.".format(thread_name))
            #SRP_LOG_DBGMSG("OVEN: Food put into the oven.");

        if stop_oven_thread:
            # reset oven_thread to default
            oven_thread_running = 0
            stop_oven_thread = 0
            print("[oven_thread({})] oven_thread() stop!".format(thread_name))
            break


# Helper function for printing changes given operation, old and new value.
def print_all_globals():
    global oven_power
    global config_temperature
    global food_inside
    global oven_temperature
    global insert_food_on_ready
    global stop_oven_thread
    global oven_thread_running
    print("global oven_power:           {}".format(oven_power))
    print("global config_temperature:   {}".format(config_temperature))
    print("global food_inside:          {}".format(food_inside))
    print("global oven_temperature:     {}".format(oven_temperature))
    print("global insert_food_on_ready: {}".format(insert_food_on_ready))
    print("global stop_oven_thread:     {}".format(stop_oven_thread))
    print("global oven_thread_running:  {}".format(oven_thread_running))

def print_change(op, old_val, new_val):
    if (op == sr.SR_OP_CREATED):
           print("\t CREATED: ",end='')
           print(new_val.to_string(),end='')
    elif (op == sr.SR_OP_DELETED):
           print("\t DELETED: ",end='')
           print(old_val.to_string(),end='')
    elif (op == sr.SR_OP_MODIFIED):
           print("\t MODIFIED: ",end='')
           print("old value",end='')
           print(old_val.to_string(),end='')
           print("new value",end='')
           print(new_val.to_string(),end='')
    elif (op == sr.SR_OP_MOVED):
        print("\t MOVED: " + new_val.xpath() + " after " + old_val.xpath())


# Helper function for printing events.
def ev_to_str(ev):
    if (ev == sr.SR_EV_CHANGE):
        return "change"
    elif (ev == sr.SR_EV_DONE):
        return "done"
    elif (ev == sr.SR_EV_VERIFY):
        return "verify"
    elif (ev == sr.SR_EV_APPLY):
        return "apply"
    elif (ev == sr.SR_EV_ABORT):
        return "abort"
    else:
        return "abort"

# Function to print current configuration state.
# It does so by loading all the items of a session and printing them out.
def print_current_config(session, select_xpath):
#    select_xpath = "/" + module_name + ":*//*"

    values = session.get_items(select_xpath)

    for i in range(values.val_cnt()):
        print(values.val(i).to_string(),end='')

#def oven_insert_food_cb(session, op_path, input, input_cnt, event, request_id, output, output_cnt, private_data):
def oven_insert_food_cb(session, path, input, event, request_id, output, private_data):


    try:
        global insert_food_on_ready
        global food_inside

        print("========== RPC CALLED for insert food START ==========")
        for i in range(input.val_cnt()):
            #print ("input: "+input.val(i).xpath())
            #print ("input: "+input.val(i).to_string())
            c_to_string = input.val(i).to_string()
            c_xpath = input.val(i).xpath()
            c_node_name = sr.Xpath_Ctx().node_name(c_xpath)
            c_val_to_string = input.val(i).val_to_string()
            print("input to_string: {}".format(c_to_string), end='')
            print("input xpath: {}".format(c_xpath))
            print("input node name: {}".format(c_node_name))
            print("input val_to_string: {}".format(c_val_to_string))

            if (food_inside):
                print("OVEN: Food already in the oven.")
                return sr.SR_ERR_OPERATION_FAILED

            if (c_node_name == "time" and c_val_to_string == "on-oven-ready"):
                if (insert_food_on_ready): 
                    print("OVEN: Food already waiting for the oven to be ready.")
                    return sr.SR_ERR_OPERATION_FAILED

                insert_food_on_ready =1
                print("\t   OVEN: Setted insert_food_on_ready=1");
                return sr.SR_ERR_OK
                
            insert_food_on_ready = 0 
            food_inside = 1
            print("\t   OVEN: Food put into the oven.");

        print("========== RPC CALLED for insert food END==========")
    
    except Exception as e:
        print(e)

    return sr.SR_ERR_OK
    

def oven_remove_food_cb(session, path, input, event, request_id, output, private_data):

    try:
        print("========== RPC CALLED for remove food START ==========")

        global food_inside
        
        if food_inside == 0:
            print("\t   OVEN: Food not in the oven.")
            return sr.SR_ERR_OPERATION_FAILED

        food_inside = 0

        print("\t   OVEN: Food taken out of the oven.");
        print("========== RPC CALLED for remove food END==========")
    
    except Exception as e:
        print(e)

    return sr.SR_ERR_OK

def update_global_oven_vars(opstr=None, \
    old_node_name=None, old_val_str=None, \
    new_node_name=None, new_val_str=None ):

    global oven_power
    global food_inside
    global insert_food_on_ready
    global oven_temperature
    global config_temperature
    
    if opstr != None :
        if opstr == "CREATED" :
            if new_node_name == "turned-on":
                oven_power = strTo1(new_val_str)

            if new_node_name == "temperature":
                config_temperature = int(new_val_str)

        elif opstr == "DELETED" :
            if old_node_name == "turned-on":
                oven_power = strTo1(new_val_str)

            if old_node_name == "temperature":
                config_temperature = int(new_val_str)

        elif opstr == "MODIFIED" :

            # In oven, we only update new_val in MODIFIED.
            if new_node_name == "turned-on":
                oven_power = strTo1(new_val_str)

            if new_node_name == "temperature":
                config_temperature = int(new_val_str)

        elif opstr == "MOVED" :
            pass
        else:
            print("\t Not a valid opstr: {}".format(opstr))

    else:
        print("\t opstr can't be None.")

    return sr.SR_ERR_OK

def oven_done():

    global oven_power
    global stop_oven_thread
    global oven_thread_running
    global oven_temperature

    if (oven_power==1 and oven_thread_running==0):
        #the oven should be turned on and is not (create the oven thread)
        stop_oven_thread = 0
        t1 = threading.Thread(target = oven_thread) 
        t1.start() 
        t1.join()
    elif (oven_power ==0 and oven_thread_running == 1):
        #the oven should be turned off but is on (stop the oven thread) 
        stop_oven_thread = 1
        #we pretend the oven cooled down immediately after being turned off
        oven_temperature = 25


    print_all_globals()
    return sr.SR_ERR_OK

def oven_change(sess, it, change, old_val, new_val):
    # while loop run at least one time.
    while change != None:
        if (change.oper() == sr.SR_OP_CREATED):
            op_string="CREATED"
            #print("\t [{}] old_val: {}, new_val: {}".format(op_string, old_val.to_string(), new_val.to_string()))
            c_xpath_old = change.old_val().xpath()
            c_node_name_old = sr.Xpath_Ctx().node_name(c_xpath_old)
            c_val_to_string_old = change.old_val().val_to_string()
            print( "\t [{}] c_xpath_old: {}".format(op_string, c_xpath_old) )
            print( "\t [{}] c_node_name_old: {}".format(op_string, c_node_name_old) )
            print( "\t [{}] c_val_to_string_old: {}".format(op_string, c_val_to_string_old) )
            c_xpath_new = change.new_val().xpath()
            c_node_name_new = sr.Xpath_Ctx().node_name(c_xpath_new)
            c_val_to_string_new = change.new_val().val_to_string()
            print( "\t [{}] c_xpath_new: {}".format(op_string, c_xpath_new) )
            print( "\t [{}] c_node_name_new: {}".format(op_string, c_node_name_new) )
            print( "\t [{}] c_val_to_string_new: {}\n".format(op_string, c_val_to_string_new) )

            # In CREATED, we only need update new_val.
            update_global_oven_vars(opstr=op_string, new_node_name=c_node_name_new, new_val_str=c_val_to_string_new)

        elif (change.oper() == sr.SR_OP_DELETED):
            op_string="DELETED"
            #print("\t [{}] old_val: {}, new_val: {}".format(op_string, old_val.to_string(), new_val.to_string()))
            c_xpath_old = change.old_val().xpath()
            c_node_name_old = sr.Xpath_Ctx().node_name(c_xpath_old)
            c_val_to_string_old = change.old_val().val_to_string()
            print( "\t [{}] c_xpath_old: {}".format(op_string, c_xpath_old) )
            print( "\t [{}] c_node_name_old: {}".format(op_string, c_node_name_old) )
            print( "\t [{}] c_val_to_string_old: {}".format(op_string, c_val_to_string_old) )
            c_xpath_new = change.new_val().xpath()
            c_node_name_new = sr.Xpath_Ctx().node_name(c_xpath_new)
            c_val_to_string_new = change.new_val().val_to_string()
            print( "\t [{}] c_xpath_new: {}".format(op_string, c_xpath_new) )
            print( "\t [{}] c_node_name_new: {}".format(op_string, c_node_name_new) )
            print( "\t [{}] c_val_to_string_new: {}\n".format(op_string, c_val_to_string_new) )

            # In DELETED, we only need update old_val.
            update_global_oven_vars(opstr=op_string, old_node_name=c_node_name_old, old_val_str=c_val_to_string_old)

        elif (change.oper() == sr.SR_OP_MODIFIED):
            op_string="MODIFIED"
            #print("\t [{}] old_val: {}, new_val: {}".format(op_string, old_val.to_string(), new_val.to_string()))
            c_xpath_old = change.old_val().xpath()
            c_node_name_old = sr.Xpath_Ctx().node_name(c_xpath_old)
            c_val_to_string_old = change.old_val().val_to_string()
            print( "\t [{}] c_xpath_old: {}".format(op_string, c_xpath_old) )
            print( "\t [{}] c_node_name_old: {}".format(op_string, c_node_name_old) )
            print( "\t [{}] c_val_to_string_old: {}".format(op_string, c_val_to_string_old) )
            c_xpath_new = change.new_val().xpath()
            c_node_name_new = sr.Xpath_Ctx().node_name(c_xpath_new)
            c_val_to_string_new = change.new_val().val_to_string()
            print( "\t [{}] c_xpath_new: {}".format(op_string, c_xpath_new) )
            print( "\t [{}] c_node_name_new: {}".format(op_string, c_node_name_new) )
            print( "\t [{}] c_val_to_string_new: {}\n".format(op_string, c_val_to_string_new) )

            # In MODIFIED, we need both old_val and new_val.
            update_global_oven_vars(opstr=op_string, \
                old_node_name=c_node_name_old, old_val_str=c_val_to_string_old, \
                new_node_name=c_node_name_new, new_val_str=c_val_to_string_new)

        elif (change.oper() == sr.SR_OP_MOVED):
            op_string="MOVED"
            #print("\t [{}] old_val: {}, new_val: {}".format(op_string, old_val.to_string(), new_val.to_string()))
            c_xpath_old = change.old_val().xpath()
            c_node_name_old = sr.Xpath_Ctx().node_name(c_xpath_old)
            c_val_to_string_old = change.old_val().val_to_string()
            print( "\t [{}] c_xpath_old: {}".format(op_string, c_xpath_old) )
            print( "\t [{}] c_node_name_old: {}".format(op_string, c_node_name_old) )
            print( "\t [{}] c_val_to_string_old: {}".format(op_string, c_val_to_string_old) )
            c_xpath_new = change.new_val().xpath()
            c_node_name_new = sr.Xpath_Ctx().node_name(c_xpath_new)
            c_val_to_string_new = change.new_val().val_to_string()
            print( "\t [{}] c_xpath_new: {}".format(op_string, c_xpath_new) )
            print( "\t [{}] c_node_name_new: {}".format(op_string, c_node_name_new) )
            print( "\t [{}] c_val_to_string_new: {}\n".format(op_string, c_val_to_string_new) )

            # In MOVED, we need both old_val and new_val, but we don't know which case hit in MOVED so we pass it now.
            #update_global_oven_vars(opstr=op_string, \
            #    old_node_name=c_node_name_old, old_val_str=c_val_to_string_old, \
            #    new_node_name=c_node_name_new, new_val_str=c_val_to_string_new)

        change = sess.get_change_next(it)

    else:
        print("\t No more {} change iterator found...End the oven_change()." )


    return sr.SR_ERR_OK

def process_change_event(sess, module_name, change_path):
    """ graber all change nodes and save it for later used inf process_done() """
    it = sess.get_changes_iter(change_path)
    if it is None:
        print("\t Get iterator failed.")
        return sr.SR_ERR_NOT_FOUND

    change = sess.get_change_next(it)
    if change == None:
        print("\t This change_path is not what we want.")
    else:
        oven_change(sess, it, change, change.old_val(), change.new_val())

    return sr.SR_ERR_OK

def process_done_event(sess, module_name, change_path):
    oven_done()
    return sr.SR_ERR_OK

# Function to be called for subscribed client of given session whenever configuration changes.
def module_change_cb(sess, module_name, xpath, event, request_id, private_data):

    try:
        #change_path = "/" + module_name + ":oven/Static-IP-Address-List/*//."
        #change_path = "/" + module_name + ":*//."
        print ("========== START module_change_cb() - Notification " + ev_to_str(event) + "\n")

        print("module_name: {}".format(module_name))
        print("xpath: {}".format(xpath))
        print("event: {}".format(event))

        '''
        if (sr.SR_EV_CHANGE == event):
            print("\n ========== CONFIG HAS CHANGED, CURRENT RUNNING CONFIG: ==========\n")
            print_current_config(sess, change_path);
        '''


        if (event == sr.SR_EV_CHANGE):
            print ("\n\n ========== IN module_change_cb() - Notification " + ev_to_str(event) + "\n")
            process_change_event(sess, module_name, xpath)

        elif (event == sr.SR_EV_DONE):
            print ("\n\n ========== IN module_change_cb() - Notification " + ev_to_str(event) + "\n")
            process_done_event(sess, module_name, xpath)

        else:
            print ("\n\n ========== IN module_change_cb() - Notification " + ev_to_str(event) + "\n")

        print ("\n\n ========== END module_change_cb() - Notification " + ev_to_str(event) + "\n")

    except Exception as e:
        print(e)

    return sr.SR_ERR_OK
def module_change_cb2(sess, module_name, xpath, event, request_id, private_data):

    try:
        print ("\n\n ========== Notification " + ev_to_str(event) + " =============================================\n")

        #change_path = "/" + module_name + ":*//."
        change_path = "/" + module_name + ":oven/ihung-test-node/*//."

        it = sess.get_changes_iter(change_path);
        if it is None:
            print("\t Get iterator failed.")
            return sr.SR_ERR_NOT_FOUND

        change_tree = sess.get_change_tree_next(it)
        new_change_tree=sr.Tree_Change()
        if change_tree == None:
            print("\t change_tree is None")
        else:
            print("repr(change_tree): {}".format(repr(change_tree))) 
            print("repr(new_change_tree): {}".format(repr(new_change_tree))) 
           # print("change_tree.oper(): {}".format(change_tree.oper()))
            print("new_change_tree.oper(): {}".format(new_change_tree.oper()))
            print("new_change_tree.node(): {}".format(new_change_tree.node()))
            print("new_change_tree.node().list_pos(): {}".format(new_change_tree.node().list_pos()))
            print("new_change_tree.prev_value(): {}".format(new_change_tree.prev_value()))
            print("new_change_tree.prev_list(): {}".format(new_change_tree.prev_list()))
            print("new_change_tree.prev_dflt(): {}".format(new_change_tree.prev_dflt()))
          #  print("change_tree.prev_value(): {}".format(new_change_tree.prev_value()))
          #  print(change_tree)

        print("\n\n ========== END OF CHANGES =======================================\n")

    except Exception as e:
        print(e)

    return sr.SR_ERR_OK

def oven_state_cb(session, module_name, path, request_xpath, request_id, parent, private_data):
    global food_inside
    global oven_temperature
    print("\n\n oven_state_cb in")
    print("\n\n ========== CALLBACK CALLED TO PROVIDE \"" + path + "\" DATA ==========")
    try:
        ctx = session.get_context()
        mod = ctx.get_module(module_name)

        print("\t /oven:oven-state")
        print("\t\t temperature {}".format(oven_temperature))
        print("\t\t food-inside {}".format('true' if food_inside == 1 else 'false'))
        parent.reset(sr.Data_Node(ctx, "/oven:oven-state", None, sr.LYD_ANYDATA_CONSTSTRING, 0))
        tmpr = sr.Data_Node(parent, mod, "temperature", "{}".format(oven_temperature))
        foodIn = sr.Data_Node(parent, mod, "food-inside", "{}".format('true' if food_inside == 1 else 'false'))

    except Exception as e:
        print(e)
        return sr.SR_ERR_OK
    sys.stdout.flush()
    return sr.SR_ERR_OK


try:
    module_name = "oven"
    if len(sys.argv) > 1:
        module_name = sys.argv[1]
    else:
        print("\nYou can pass the module name to be subscribed as the first argument")

    print("Application will watch for changes in " +  module_name + "\n")

    # connect to sysrepo
    conn = sr.Connection(sr.SR_CONN_DEFAULT)

    # start session
    sess = sr.Session(conn)

    # subscribe for changes in running config */
    subscribe = sr.Subscribe(sess)

    #subscribe.module_change_subscribe(module_name, module_change_cb, None, None, 0, sr.SR_SUBSCR_DONE_ONLY)
    #subscribe.module_change_subscribe(module_name, module_change_cb2, None, None, 0, sr.SR_SUBSCR_DONE_ONLY|sr.SR_SUBSCR_ENABLED)
    subscribe.module_change_subscribe(module_name, module_change_cb, "/oven:oven//.", None, 0, 0)

    #subscribe.rpc_subscribe("/oven:insert-food", oven_insert_food_cb, sr.SR_SUBSCR_CTX_REUSE)
    #subscribe.rpc_subscribe("/oven:remove-food", oven_remove_food_cb, sr.SR_SUBSCR_CTX_REUSE)
    subscribe.rpc_subscribe("/oven:insert-food", oven_insert_food_cb, None, 0, sr.SR_SUBSCR_CTX_REUSE)
    subscribe.rpc_subscribe("/oven:remove-food", oven_remove_food_cb, None, 0, sr.SR_SUBSCR_CTX_REUSE)
    #subscribe.rpc_subscribe("/oven:insert-food", oven_insert_food_cb)
    #subscribe.rpc_subscribe("/oven:remove-food", oven_remove_food_cb)

    subscribe.oper_get_items_subscribe(module_name, "/oven:oven-state", oven_state_cb, None, sr.SR_SUBSCR_CTX_REUSE)

    print("\n\n ========== READING RUNNING CONFIG: ==========\n")
    try:
        select_xpath = "/" + module_name + ":*//*"
        print_current_config(sess, select_xpath);
    except Exception as e:
        print(e)

    sr.global_loop()
    
    subscribe.unsubscribe()

    sess.session_stop()

    conn=None

    print("Application exit requested, exiting.\n")

except Exception as e:
    print(e)

