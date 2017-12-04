#!/usr/bin/env python
##
## A. Rothkirch, FSEC, Aug 02, 2017.
##
## history:
##
## version 0: a first draft, A.R.
##

import struct
import numpy as np

def eval_tif_blob(blob, debug=0):
	image=np.float(-1)
	sample_format=1	# define unsigned default if undefined - i.e. like MAR165 data
	blob_endian='none'
	if (sum(abs(blob[0:2]-[73,73])) == 0):
		blob_endian="<"	# little
	if (sum(abs(blob[0:2]-[77,77])) == 0):
		blob_endian=">" #  big

	if (blob_endian == "none"):
		if debug == 1: print 'Endianess unknown (or not a tiff blob)'
		return image	 # or better to raise exception?

	numfortiff=np.uint16(struct.unpack_from(blob_endian+"H", blob[2:4])[0])
	if (numfortiff != 42):
		if debug == 1: print 'Invalid tiff identifier'
		return image  # or better to raise exception?

	ifd_off=np.uint32(struct.unpack_from(blob_endian+"I", blob[4:8])[0])
	#
	#jump to/eval image file directory (ifd)
	num_of_ifd=np.uint16(struct.unpack_from(blob_endian+"H", blob[ifd_off:ifd_off+2])[0])
	if debug == 1: print 'ifd entires existent: '+str(num_of_ifd)

	for ifd_entry in range(num_of_ifd):
		field_tag=np.uint16(struct.unpack_from(blob_endian+"H", blob[ifd_off+2+ifd_entry*12:ifd_off+4+ifd_entry*12])[0])
		field_type=np.uint16(struct.unpack_from(blob_endian+"H", blob[ifd_off+4+ifd_entry*12:ifd_off+6+ifd_entry*12])[0])
		num_vals=np.uint32(struct.unpack_from(blob_endian+"I", blob[ifd_off+6+ifd_entry*12:ifd_off+10+ifd_entry*12])[0])
		## given tiff 6.0 there are 12 type entries, currently not all of them are accounted, A.R.
		val_or_off=0
		if (field_type == 1):	# check blob addressing!
			val_or_off=np.uint8(struct.unpack_from(blob_endian+"B", blob[ifd_off+10+ifd_entry*12:ifd_off+15+ifd_entry*12])[0])
		if (field_type == 3):
			val_or_off=np.uint16(struct.unpack_from(blob_endian+"H", blob[ifd_off+10+ifd_entry*12:ifd_off+15+ifd_entry*12])[0])
		if (field_type == 4):
			val_or_off=np.uint32(struct.unpack_from(blob_endian+"I", blob[ifd_off+10+ifd_entry*12:ifd_off+15+ifd_entry*12])[0])
		if (field_type == 8):
			val_or_off=np.int16(struct.unpack_from(blob_endian+"h", blob[ifd_off+10+ifd_entry*12:ifd_off+15+ifd_entry*12])[0])
		if (field_type == 9):
			val_or_off=np.int32(struct.unpack_from(blob_endian+"i", blob[ifd_off+10+ifd_entry*12:ifd_off+15+ifd_entry*12])[0])
		if (field_type == 11):
			val_or_off=np.float32(struct.unpack_from(blob_endian+"f", blob[ifd_off+10+ifd_entry*12:ifd_off+15+ifd_entry*12])[0])

		if debug == 1: 
			print 'ifd entry'+str(ifd_entry)
			print field_tag, field_type, num_vals, val_or_off

		# eval (hopefully) tags needed to allow for getting an image
		if (field_tag == 256):
			width=val_or_off
		if (field_tag == 257):
			length=val_or_off
		if (field_tag == 258):
			bit_per_sample=val_or_off
		## compression scheme - return invalid if NOT none,
		## i.e. only uncompressed data is supported (forever!?)
		if (field_tag == 259):
			if (val_or_off != 1):
				if debug == 1: print 'Data compression is NOT none - unsupported'
				return image
		## photometric interpretation - 2 denotes RGB which is refused
		## otherwise don't mind/care ...
		if (field_tag == 262):
			if (val_or_off == 2):
				if debug == 1: print 'Data is RGB - unsupported'
				return image
		if (field_tag == 273):
			strip_offsets=val_or_off
		# likely equals image width
		if (field_tag == 278):
			rows_per_strip=val_or_off
		if (field_tag == 279):
			strip_byte_counts=val_or_off
		if (field_tag == 339):
			sample_format=val_or_off

		next_idf=np.uint32(struct.unpack_from(blob_endian+"I", blob[ifd_off+15+(num_of_ifd+1)*12:ifd_off+19+(num_of_ifd+1)*12])[0])
		if (next_idf != 0):
			print 'another ifd exists ... NOT read'

	if ((width*length*bit_per_sample/8) != strip_byte_counts):
		if debug == 1: print 'Invalid tiff identifier'
		return image

	if sample_format == 1 and bit_per_sample == 8:
		image=np.uint8(struct.unpack_from(blob_endian+str(width*length)+"B", blob[strip_offsets:strip_offsets+strip_byte_counts+1]))
	if sample_format == 1 and bit_per_sample == 16:
		image=np.uint16(struct.unpack_from(blob_endian+str(width*length)+"H", blob[strip_offsets:strip_offsets+strip_byte_counts+1]))
	if sample_format == 1 and bit_per_sample == 32:
		image=np.uint32(struct.unpack_from(blob_endian+str(width*length)+"I", blob[strip_offsets:strip_offsets+strip_byte_counts+1]))
#	if sample_format == 2 and bit_per_sample == 8:
#		image=np.int8(struct.unpack_from(blob_endian+str(width*length)+"b", blob[strip_offsets:strip_offsets+strip_byte_counts+1]))
	if sample_format == 2 and bit_per_sample == 16:
		image=np.int16(struct.unpack_from(blob_endian+str(width*length)+"h", blob[strip_offsets:strip_offsets+strip_byte_counts+1]))
	if sample_format == 2 and bit_per_sample == 32:
		image=np.int32(struct.unpack_from(blob_endian+str(width*length)+"i", blob[strip_offsets:strip_offsets+strip_byte_counts+1]))
	if sample_format == 3 and bit_per_sample == 32:
		image=np.float32(struct.unpack_from(blob_endian+str(width*length)+"f", blob[strip_offsets:strip_offsets+strip_byte_counts+1]))

	try:
		return image.reshape(width,length,order='F')
	except:
		if debug == 1: print 'Something went wrong, e.g. recommended tags missingor nsupported sample format or ...'
		return image


#### sample data sets for testing
## lost_... is a Pilatus 300k tif file
## mar165_... is an image taken with MAR165 detector and x2 binning applied
#filename = '/afs/desy.de/user/r/rothkirc/public/P03/lost_00001_00001.tif'  # input file name
filename = '/afs/desy.de/user/r/rothkirc/public/20131129_eugen/mar165_agbeh_00001.tif'  # input file name

tmp = np.fromfile(filename, dtype='uint8')    # read all content as unit 8

res=eval_tif_blob(tmp)
print "Return value shape and dtype"
print res.shape, res.dtype

