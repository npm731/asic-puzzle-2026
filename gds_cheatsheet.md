# `.gds` file cheatsheet

[Original Stream Format Manual](http://bitsavers.informatik.uni-stuttgart.de/pdf/calma/GDS_II_Stream_Format_Manual_6.0_Feb87.pdf), but there's also this one that's got a bit of analysis.

[The GDSII Stream Format](https://web.archive.org/web/20160616215711/http://www.buchanan1.net/stream_description.html)


## Basics
Files were historically written as streams to 9 different drives onto magnetic tapes in 2048 byte physical blocks (Size `0x800`), but records may overlap physical block boundaries (though often they were NULL'd to the end of the block if needed?)

File consists of `records` made of 16-bit, 2 byte "words". Each `record` is 4 or more bytes.

Interestingly `.gds` is big endian. So for the `int16` value `0xBEEF` it would appears as `BE EF` in the hex dump, while in typical `.dis` it would be `EF BE`. 

The first two words (4B) is the "Record Header"
- first two bytes are the record length
- third byte is record type
- fourth byte is the data type


Null word is two consecutive 0 bytes. Null record is two null words? 


### Data types

| Value 	| Data Type                          	|
|-------	|------------------------------------	|
| 0     	| No data                            	|
| 1     	| bit array (depends on record type) 	|
| 2     	| Two byte signed int                	|
| 3     	| Four byte signed int               	|
| 6     	| ASC-II (odd length strings padded with `0x00`)|


### Record Types

- 0: HEADER, always contains two bytes for version number. `0x258` is version `6.0`



## Exmaple
E.g. For the first 8 bytes here
```
00 06 00 02 02 58 00 1c
```
This has a record length of `0x6` which means the record is 6 bytes long:
```
00 06 00 02 02 58
```
The Record Type is `0x0` (HEADER) and the data type is `0x2` which is two bytes signed int, or `int16`.
The remainder of the record is `0x0258`.
