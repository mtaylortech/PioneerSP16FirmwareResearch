import pathlib,struct,zlib,binascii,sys
p=pathlib.Path(sys.argv[1]);data=p.read_bytes();h=struct.unpack_from('>25I',data);size,version,fmt,depth,w,height,xoffset,order,unit,bitorder,pad,bpp,stride,vclass,red,green,blue,bits,cmap,ncolors,*_=h
assert version==7 and fmt==2 and xoffset==0 and bpp==32
pixels=data[size+ncolors*12:];assert len(pixels)==height*stride
scan=bytearray()
shifts=[(m&-m).bit_length()-1 for m in (red,green,blue)]
for y in range(height):
 scan.append(0)
 for x in range(w):
  word=int.from_bytes(pixels[y*stride+x*4:y*stride+x*4+4],'little' if order==0 else 'big')
  scan.extend(((word&m)>>s for m,s in zip((red,green,blue),shifts)))
def chunk(t,b):return struct.pack('>I',len(b))+t+b+struct.pack('>I',binascii.crc32(t+b)&0xffffffff)
output=pathlib.Path(sys.argv[2]);output.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',w,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(scan))+chunk(b'IEND',b''));print(output)
