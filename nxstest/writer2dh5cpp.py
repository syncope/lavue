from pninexus import h5cpp
import numpy as np
import time


# a new file name
filename = "swmr.h5"

# data, their shape and chunk
arr = np.array([[1, 2, 3], [4, 5, 6]])
shape = [0, 3, 2]
chunk = [1, 3, 2]


# set the SWMRWRITE and TR UNCATE flags
flag = h5cpp.file.AccessFlags.TRUNCATE | h5cpp.file.AccessFlags.SWMRWRITE

fcpl = h5cpp.property.FileCreationList()

fapl = h5cpp.property.FileAccessList()
fapl.set_close_degree(h5cpp._property.CloseDegree.STRONG)
# open file with latest h5cpp version
fapl.library_version_bounds(h5cpp.property.LibVersion.LATEST,
                            h5cpp.property.LibVersion.LATEST)

# create a file
hfile = h5cpp.file.create(filename, flag, fcpl, fapl)
rt = hfile.root()

# create a field
dcpl = h5cpp.property.DatasetCreationList()
dataspace = h5cpp.dataspace.Simple(
    tuple(shape), tuple([h5cpp.dataspace.UNLIMITED] * len(shape)))
dcpl.layout = h5cpp.property.DatasetLayout.CHUNKED
dcpl.chunk = tuple(chunk)
field = h5cpp.node.Dataset(rt, h5cpp.Path("data"),
                           h5cpp.datatype.kInt64, dataspace, dcpl=dcpl)

# write data in chuncks
for i in range(50):
    print(i)
    field.extent(0, 1)
    selection = h5cpp.dataspace.Hyperslab(offset=(i, 0, 0), block=chunk)
    field.write(arr + i, selection)
    # flush the data
    hfile.flush()
    time.sleep(1)
hfile.close()
