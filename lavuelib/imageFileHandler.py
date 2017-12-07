# Copyright (C) 2017  DESY, Christoph Rosemann, Notkestr. 85, D-22607 Hamburg
#
# lavue is an image viewing program for photon science imaging detectors.
# Its usual application is as a live viewer using hidra as data source.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation in  version 2
# of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.
#
# Authors:
#     Christoph Rosemann <christoph.rosemann@desy.de>
#     Andre Rothkirch <andre.rothkirch@desy.de>
#     Jan Kotanski <jan.kotanski@desy.de>
#

""" this a simple file handler that loads image files
    and delivers just the actual array """

import struct
import numpy as np

try:
    import fabio
    FABIO = True
except ImportError:
    FABIO = False
try:
    import PIL
    PILLOW = True
except ImportError:
    PILLOW = False


class ImageFileHandler(object):

    """Simple file handler class.
       Reads image from file and returns the numpy array."""

    def __init__(self, fname):
        self._image = None
        self._data = None
        try:
            if FABIO:
                self._image = fabio.open(fname)
                self._data = self._image.data
            elif PILLOW:
                self._image = PIL.Image.open(fname)
                self._data = np.array(self._image)
        except Exception:
            try:
                if FABIO and PILLOW:
                    self._image = PIL.Image.open(fname)
                    self._data = np.array(self._image)
            except Exception:
                try:
                    self._image = np.fromfile(filename, dtype='uint8')
                    if fname.endswith(".cbf"):
                        self._data = CBFLoader().load(self._image)
                    else:
                        self._data = TIFLoader().load(self._image)
                except Exception:
                    pass

    def getImage(self):
        return self._data


class CBFLoader(object):

    @classmethod
    def load(cls, flbuffer):
        image = np.array([0])
        inpoint = np.array([26, 4, 213], dtype='uint8')
        outpoint = np.array(
            [45, 45, 67, 73, 70, 45, 66, 73, 78, 65, 82, 89, 45, 70,
             79, 82, 77, 65, 84, 45, 83, 69, 67, 84, 73, 79, 78, 45, 45, 45],
            dtype='uint8')
        flag = 0

        # check if byte offset compress
        boc = np.array(
            [120, 45, 67, 66, 70, 95, 66, 89, 84,
             69, 95, 79, 70, 70, 83, 69, 84],
            dtype='uint8')

        try:
            # iscbf
            flbuffer.tostring().index(boc.tostring()) // flbuffer.itemsize
        except Exception:
            flag = 1

        # additional parms for cross check if decompress worked out
        dset_num_ele = np.array(
            [88, 45, 66, 105, 110, 97, 114, 121, 45, 78, 117, 109, 98,
             101, 114, 45, 111, 102, 45, 69, 108, 101, 109, 101, 110,
             116, 115, 58],
            dtype='uint8')
        dset_fast_dim = np.array(
            [88, 45, 66, 105, 110, 97, 114, 121, 45, 83, 105, 122, 101, 45, 70,
             97, 115, 116, 101, 115, 116, 45, 68, 105, 109, 101, 110, 115, 105,
             111, 110, 58], dtype='uint8')
        dset_sec_dim = np.array(
            [88, 45, 66, 105, 110, 97, 114, 121, 45, 83, 105, 122, 101, 45, 83,
             101, 99, 111, 110, 100, 45, 68, 105, 109, 101, 110, 115, 105, 111,
             110, 58], dtype='uint8')
        dset_pad = np.array(
            [88, 45, 66, 105, 110, 97, 114, 121, 45, 83, 105, 122, 101, 45, 80,
             97, 100, 100, 105, 110, 103, 58], dtype='uint8')

        # search for data stream start
        if flag == 0:
            try:
                idstart = flbuffer.tostring().index(
                    inpoint.tostring()) // flbuffer.itemsize
                idstart += inpoint.size
            except Exception:
                flag = 1

            try:
                idstop = flbuffer.tostring().index(
                    outpoint.tostring()) // flbuffer.itemsize
                idstop -= 3  # cr / extra -1 due to '10B' -- linefeed
            except Exception:
                flag = 1

            vals = np.zeros(4, dtype='int')
            spos = np.zeros(5, dtype='int')
            spos[4] = idstart
            try:
                spos[0] = flbuffer.tostring().index(
                    dset_num_ele.tostring()) // flbuffer.itemsize
                spos[1] = flbuffer.tostring().index(
                    dset_fast_dim.tostring()) // flbuffer.itemsize
                spos[2] = flbuffer.tostring().index(
                    dset_sec_dim.tostring()) // flbuffer.itemsize
                spos[3] = flbuffer.tostring().index(
                    dset_pad.tostring()) // flbuffer.itemsize
# by A.R., Apr 24, 2017
                vals[0] = int(
                    flbuffer[
                        spos[0] + dset_num_ele.size:spos[1] - 2].tostring())
                vals[1] = int(
                    flbuffer[
                        spos[1] + dset_fast_dim.size:spos[2] - 2].tostring())
                vals[2] = int(
                    flbuffer[
                        spos[2] + dset_sec_dim.size:spos[3] - 2].tostring())
                vals[3] = int(
                    flbuffer[
                        spos[3] + dset_pad.size:spos[4] - 8].tostring())
            except Exception:
                flag = 1

            if flag == 0:
                image = 0
                image = cls._decompress_cbf_c(
                    flbuffer[idstart:idstop + 1], vals)
            else:
                image = np.array([0])
        return image

    @classmethod
    def _decompress_cbf_c(cls, stream, vals):
        xdim = long(487)
        ydim = 619
        padding = long(4095)
        n_out = xdim * ydim

        # simply assume content fits here
        if vals.size == 4 and sum(vals) != 0:
            xdim = vals[1]
            ydim = vals[2]
            padding = vals[3]
            n_out = vals[0]

        flbuffer = np.zeros(stream.size, dtype='int32') + stream
        mymap = np.zeros(stream.size, dtype='uint8') + 1
        isvalid = np.zeros(stream.size, dtype='uint8') + 1

        id_relevant = np.where(stream == 128)

        # overcome issue if 128 exists in padding (seems so that
        # either this does not happened before or padding was 0 in any case)
        try:
            idd = np.where(id_relevant < (flbuffer.size - padding))
            id_relevant = id_relevant[idd]
        except:
            pass

        for dummy, dummy2 in enumerate(id_relevant):
            for j, i in enumerate(dummy2):
                if mymap[i] != 0:
                    if stream[i + 1] != 0 or stream[i + 2] != 128:
                        mymap[i:i + 3] = 0
                        isvalid[i + 1:i + 3] = 0
                        delta = flbuffer[i + 1] + flbuffer[i + 2] * 256
                        if delta > 32768:
                            delta -= 65536
                        flbuffer[i] = delta
                    else:
                        mymap[i:i + 7] = 0
                        isvalid[i + 1:i + 7] = 0
                        # delta=sum(np.multiply(flbuffer[i+3:i+7],
                        #   np.array([1,256,65536,16777216],dtype='int64')))
                        delta = (
                            np.multiply(
                                flbuffer[i + 3:i + 7],
                                np.array([1, 256, 65536, 16777216],
                                         dtype='int64'))).sum()
                        if delta > 2147483648:
                            delta -= 4294967296
                        flbuffer[i] = delta

        try:
            id8sign = np.where((stream > 128) & (mymap != 0))
            flbuffer[id8sign] -= 256
            # print ("adjusting 8Bit vals")
            # for i, j in enumerate(stream):
            #     if j > 128 and mymap[i] !=0:
            #         flbuffer[i]=flbuffer[i]-256
            # print stream[0:11]
            # print flbuffer[0:11]

        except:
            pass

        try:
            # print sum(isvalid)    #should be 305548
            id = np.where(isvalid != 0)
            flbuffer = flbuffer[id]
        except:
            pass

        # print stream[0:11]
        # print flbuffer[0:11]

        res = np.cumsum(flbuffer, dtype='int32')
        # print max(res)

        if res.size - padding != n_out:
            return np.array([0])
        # by A.R., Apr 24, 2017
        # return res[0:n_out].reshape(xdim, ydim)
        return res[0:n_out].reshape(xdim, ydim, order='F')


class TIFLoader(object):

    @classmethod
    def load(cls, flbuffer):
        image = np.float(-1)
        # define unsigned default if undefined - i.e. like MAR165 data
        sample_format = 1
        flbuffer_endian = 'none'
        if sum(abs(flbuffer[0:2] - [73, 73])) == 0:
            flbuffer_endian = "<"  # little
        if sum(abs(flbuffer[0:2] - [77, 77])) == 0:
            flbuffer_endian = ">"  # big

        if flbuffer_endian == "none":
            return image     # or better to raise exception?

        numfortiff = np.uint16(
            struct.unpack_from(flbuffer_endian + "H", flbuffer[2:4])[0])
        if numfortiff != 42:
            return image  # or better to raise exception?

        ifd_off = np.uint32(
            struct.unpack_from(flbuffer_endian + "I", flbuffer[4:8])[0])
        #
        # jump to/eval image file directory (ifd)
        num_of_ifd = np.uint16(
            struct.unpack_from(
                flbuffer_endian + "H", flbuffer[ifd_off:ifd_off + 2])[0])

        for ifd_entry in range(num_of_ifd):
            field_tag = np.uint16(
                struct.unpack_from(
                    flbuffer_endian + "H",
                    flbuffer[ifd_off + 2 + ifd_entry * 12:ifd_off
                             + 4 + ifd_entry * 12])[0])
            field_type = np.uint16(
                struct.unpack_from(
                    flbuffer_endian + "H",
                    flbuffer[ifd_off + 4 + ifd_entry * 12:ifd_off
                             + 6 + ifd_entry * 12])[0])
            # num_vals = np.uint32(
            #    struct.unpack_from(
            #        flbuffer_endian + "I",
            #        flbuffer[ifd_off + 6 + ifd_entry * 12:ifd_off + 10
            #                 + ifd_entry * 12])[0])
            # given tiff 6.0 there are 12 type entries, currently not all of
            # them are accounted, A.R.
            val_or_off = 0
            if field_type == 1:  # check flbuffer addressing!
                val_or_off = np.uint8(
                    struct.unpack_from(
                        flbuffer_endian + "B",
                        flbuffer[ifd_off + 10 + ifd_entry * 12:ifd_off + 15
                                 + ifd_entry * 12])[0])
            if field_type == 3:
                val_or_off = np.uint16(
                    struct.unpack_from(
                        flbuffer_endian + "H",
                        flbuffer[ifd_off + 10 + ifd_entry * 12:ifd_off + 15
                                 + ifd_entry * 12])[0])
            if field_type == 4:
                val_or_off = np.uint32(
                    struct.unpack_from(
                        flbuffer_endian + "I",
                        flbuffer[ifd_off + 10 + ifd_entry * 12:ifd_off + 15
                                 + ifd_entry * 12])[0])
            if field_type == 8:
                val_or_off = np.int16(
                    struct.unpack_from(
                        flbuffer_endian + "h",
                        flbuffer[ifd_off + 10 + ifd_entry * 12:ifd_off
                                 + 15 + ifd_entry * 12])[0])
            if field_type == 9:
                val_or_off = np.int32(
                    struct.unpack_from(
                        flbuffer_endian + "i",
                        flbuffer[ifd_off + 10 + ifd_entry * 12:ifd_off + 15
                                 + ifd_entry * 12])[0])
            if field_type == 11:
                val_or_off = np.float32(
                    struct.unpack_from(
                        flbuffer_endian + "f",
                        flbuffer[ifd_off + 10 + ifd_entry * 12:ifd_off
                                 + 15 + ifd_entry * 12])[0])

            # eval (hopefully) tags needed to allow for getting an image
            if field_tag == 256:
                width = val_or_off
            if field_tag == 257:
                length = val_or_off
            if field_tag == 258:
                bit_per_sample = val_or_off
            # compression scheme - return invalid if NOT none,
            # i.e. only uncompressed data is supported (forever!?)
            if field_tag == 259:
                if val_or_off != 1:
                    return image
            # photometric interpretation - 2 denotes RGB which is refused
            # otherwise don't mind/care ...
            if field_tag == 262:
                if val_or_off == 2:
                    return image
            if field_tag == 273:
                strip_offsets = val_or_off
            # likely equals image width
            # if field_tag == 278:
            #    rows_per_strip = val_or_off
            if field_tag == 279:
                strip_byte_counts = val_or_off
            if field_tag == 339:
                sample_format = val_or_off

            next_idf = np.uint32(
                struct.unpack_from(
                    flbuffer_endian + "I",
                    flbuffer[
                        ifd_off + 15 + (num_of_ifd + 1) * 12:ifd_off + 19
                        + (num_of_ifd + 1) * 12])[0])
            if next_idf != 0:
                print('another ifd exists ... NOT read')

        if width * length * bit_per_sample / 8 != strip_byte_counts:
            return image

        if sample_format == 1 and bit_per_sample == 8:
            image = np.uint8(
                struct.unpack_from(
                    flbuffer_endian + str(width * length) + "B",
                    flbuffer[strip_offsets:strip_offsets
                             + strip_byte_counts + 1]))
        if sample_format == 1 and bit_per_sample == 16:
            image = np.uint16(
                struct.unpack_from(
                    flbuffer_endian + str(width * length) + "H",
                    flbuffer[strip_offsets:strip_offsets
                             + strip_byte_counts + 1]))
        if sample_format == 1 and bit_per_sample == 32:
            image = np.uint32(
                struct.unpack_from(
                    flbuffer_endian + str(width * length) + "I",
                    flbuffer[strip_offsets:strip_offsets
                             + strip_byte_counts + 1]))
        # if sample_format == 2 and bit_per_sample == 8:
        #     image=np.int8(struct.unpack_from(
        #           flbuffer_endian+str(width*length)+"b",
        #     flbuffer[strip_offsets:strip_offsets
        #              +strip_byte_counts+1]))
        if sample_format == 2 and bit_per_sample == 16:
            image = np.int16(
                struct.unpack_from(
                    flbuffer_endian + str(width * length) + "h",
                    flbuffer[strip_offsets:strip_offsets
                             + strip_byte_counts + 1]))
        if sample_format == 2 and bit_per_sample == 32:
            image = np.int32(
                struct.unpack_from(
                    flbuffer_endian + str(width * length) + "i",
                    flbuffer[strip_offsets:strip_offsets
                             + strip_byte_counts + 1]))
        if sample_format == 3 and bit_per_sample == 32:
            image = np.float32(
                struct.unpack_from(
                    flbuffer_endian + str(width * length) + "f",
                    flbuffer[strip_offsets:strip_offsets
                             + strip_byte_counts + 1]))

        try:
            return image.reshape(width, length, order='F')
        except:
            return image


if __name__ == "__main__":

    # filename =
    # '/afs/desy.de/user/r/rothkirc/public/P03/lost_00001_00001.tif' # input
    # file name
    # input file name
    filename = '/afs/desy.de/user/r/rothkirc/public/20131129_eugen/' \
               + 'mar165_agbeh_00001.tif'

    tmp = np.fromfile(filename, dtype='uint8')  # read all content as unit 8
    resu = TIFLoader().load(tmp)
    print("Return value shape and dtype")
    print("%s %s" % (resu.shape, resu.dtype))
