#
# author: Ch. Rosemann, DESY
# email: christoph.rosemann@desy.de

try:
    import hidra
except ImportError:
    print("without hidra installed this does not make sense")


class HiDRA_cbf_source():

    def __init__(self, signal_host=None, target=None):
        self.signal_host = signal_host
        self.target = target
        self.query = hidra.Transfer("QUERY_NEXT", signal_host)
        
    def getTargetSignalHost(self):
        return self.target[0], self.signal_host

    def connect(self):
        try:
            self.query.initiate(self.target)
            self.query.start()
            return True
        except:
            if self.query is not None:
                self.query.stop()   
            return False

    def disconnect(self):
        try:
            self.query.stop()
        except:
            pass

    def getData(self):
        metadata = None
        data = None
        try:
            [metadata, data] = self.query.get(2000)
        except:
            pass # this needs a bit more care

        if metadata is not None and data is not None:
            print ("metadata", metadata["filename"])
            print ("data", str(data)[:10])

            if (data[:10] == "###CBF: VE"):
                img = self.eval_pildata(np.fromstring(data[:], dtype=np.uint8))
                return img, metadata["filename"]
        else:
            return None, None

    def decompress_cbf_c(self, stream, vals):
        xdim = long(487)
        ydim = 619
        padding = long(4095)
        n_out = xdim * ydim

        if (vals.size == 4 and sum(vals) != 0):  # simply assume content fits here
            xdim = vals[1]
            ydim = vals[2]
            padding = vals[3]
            n_out = vals[0]

        tmp = np.zeros(stream.size, dtype='int32') + stream
        mymap = np.zeros(stream.size, dtype='uint8') + 1
        isvalid = np.zeros(stream.size, dtype='uint8') + 1

        id_relevant = np.where(stream == 128)

        # overcome issue if 128 exists in padding (seems so that
        # either this does not happened before or padding was 0 in any case)
        try:
            idd = np.where(id_relevant < (tmp.size - padding))
            id_relevant = id_relevant[idd]
        except:
            pass

        for dummy, dummy2 in enumerate(id_relevant):
            for j, i in enumerate(dummy2):
                if (mymap[i] != 0):
                    if(stream[i + 1] != 0 or stream[i + 2] != 128):
                        mymap[i:i + 3] = 0
                        isvalid[i + 1:i + 3] = 0
                        delta = tmp[i + 1] + tmp[i + 2] * 256
                        if (delta > 32768):
                            delta -= 65536
                        tmp[i] = delta
                    else:
                        mymap[i:i + 7] = 0
                        isvalid[i + 1:i + 7] = 0
    #					delta=sum(np.multiply(tmp[i+3:i+7],np.array([1,256,65536,16777216],dtype='int64')))
                        delta = (
                            np.multiply(tmp[i + 3:i + 7], np.array([1, 256, 65536, 16777216], dtype='int64'))).sum()
                        if (delta > 2147483648):
                            delta -= 4294967296
                        tmp[i] = delta

        try:
            id8sign = np.where((stream > 128) & (mymap != 0))
            tmp[id8sign] -= 256
            # print ("adjusting 8Bit vals")
            # for i, j in enumerate(stream):
            #	if ( j > 128 and mymap[i] !=0):
            #		tmp[i]=tmp[i]-256
            # print stream[0:11]
            # print tmp[0:11]

        except:
            print ("error debug1")
            pass

        try:
            # print sum(isvalid)	#should be 305548
            id = np.where(isvalid != 0)
            tmp = tmp[id]
        except:
            pass

        # print stream[0:11]
        # print tmp[0:11]

        res = np.cumsum(tmp, dtype='int32')
        # print max(res)

        if ((res.size - padding) != n_out):
            return np.array([0])

        return res[0:n_out].reshape(xdim, ydim)


    def eval_pildata(self, tmp):
        image = np.array([0])
        inpoint = np.array([26, 4, 213], dtype='uint8')
        outpoint = np.array(
            [45, 45, 67, 73, 70, 45, 66, 73, 78, 65, 82, 89, 45, 70,
             79, 82, 77, 65, 84, 45, 83, 69, 67, 84, 73, 79, 78, 45, 45, 45], dtype='uint8')
        flag = 0

        # check if byte offset compress
        boc = np.array(
            [120, 45, 67, 66, 70, 95, 66, 89, 84, 69, 95, 79, 70, 70, 83, 69, 84], dtype='uint8')

        try:
            iscbf = tmp.tostring().index(boc.tostring()) // tmp.itemsize
        except:
            flag = 1

        # additional parms for cross check if decompress worked out
        dset_num_ele = np.array(
            [88, 45, 66, 105, 110, 97, 114, 121, 45, 78, 117, 109, 98,
             101, 114, 45, 111, 102, 45, 69, 108, 101, 109, 101, 110, 116, 115, 58], dtype='uint8')
        dset_fast_dim = np.array(
            [88, 45, 66, 105, 110, 97, 114, 121, 45, 83, 105, 122, 101, 45, 70, 97,
             115, 116, 101, 115, 116, 45, 68, 105, 109, 101, 110, 115, 105, 111, 110, 58], dtype='uint8')
        dset_sec_dim = np.array(
            [88, 45, 66, 105, 110, 97, 114, 121, 45, 83, 105, 122, 101, 45, 83,
             101, 99, 111, 110, 100, 45, 68, 105, 109, 101, 110, 115, 105, 111, 110, 58], dtype='uint8')
        dset_pad = np.array(
            [88, 45, 66, 105, 110, 97, 114, 121, 45, 83, 105, 122, 101, 45, 80, 97, 100, 100, 105, 110, 103, 58], dtype='uint8')

        # search for data stream start
        if (flag == 0):
            try:
                idstart = tmp.tostring().index(
                    inpoint.tostring()) // tmp.itemsize
                idstart += inpoint.size
            except:
                flag = 1

            try:
                idstop = tmp.tostring().index(
                    outpoint.tostring()) // tmp.itemsize
                idstop -= 3  # cr / extra -1 due to '10B' -- linefeed
            except:
                flag = 1

            vals = np.zeros(4, dtype='int')
            spos = np.zeros(5, dtype='int')
            spos[4] = idstart
            try:
                spos[0] = tmp.tostring().index(
                    dset_num_ele.tostring()) // tmp.itemsize
                spos[1] = tmp.tostring().index(
                    dset_fast_dim.tostring()) // tmp.itemsize
                spos[2] = tmp.tostring().index(
                    dset_sec_dim.tostring()) // tmp.itemsize
                spos[3] = tmp.tostring().index(
                    dset_pad.tostring()) // tmp.itemsize
            except:
                flag = 1

            if (flag == 0):
                image = 0
                image = self.decompress_cbf_c(tmp[idstart:idstop + 1], vals)
            else:
                image = np.array([0])
        return image


if __name__ == "__main__":
    target = [socket.getfqdn(), "50101", 19, [".cbf"]]
    signal_host = "haspp10pilatus.desy.de"

    source = HiDRA_cbf_source(mystery.signal_host, mystery.target)
