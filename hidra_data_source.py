#
# author: Ch. Rosemann, DESY
# email: christoph.rosemann@desy.de

try:
    import hidra
except ImportError:
    print("without hidra installed this does not make sense")


class HiDRA_data_source():
    def __init__(self):
        self.signal_host = None
        self.target = None
        self.query = None
        
    def configure(self, signal_host, target):
        self.signal_host = signal_host
        self.target = target
    
    def connect
        
    
def establish_hidra_connection(signal_host=None, target=None):
    try:
        query = hidra.Transfer("QUERY_NEXT", signal_host)
        query.initiate(target)
        query.start()
        return True
    except:
        query.stop()	# remove list entry established by query.initiate()
        sys.exit(255)	# exit - should be replaced by retrying query with other port

