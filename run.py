# run the whole project from here
# clear mn
'sudo mn -c'
# run controller
'sudo ryu-manager --observe-links main.py'
# run constum ropology
'sudo python new_dtopo.py'
# calculate slope of flowtable changes
'sudo python3 flow_table_update_rate.py'