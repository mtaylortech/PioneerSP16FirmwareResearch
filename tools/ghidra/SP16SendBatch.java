// ---------------------------------------------------------------------------
// SP-16 open research — original research Ghidra script, unchanged below.
// Ghidra script from the Mixer Send widget investigation (batch annotations/exports).
// Original path: ghidra/scripts/SP16SendBatch.java
// Original SHA-256: 52aced13c0d78e511d02c5935d1d945944758e6a8fe89b1dcb83e670ae030147
// License: MIT (see repository LICENSE). Addresses refer to the firmware
// version named in the script/docs; they are wrong for other versions.
// ---------------------------------------------------------------------------
//@category PioneerSP16
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.data.*;
import com.google.gson.*;
import java.nio.file.*;
import java.util.*;
import java.math.BigInteger;

public class SP16SendBatch extends GhidraScript {
 final String CATEGORY="/SP16_SendBatch_20261009";
 void require(boolean ok,String why){if(!ok)throw new IllegalStateException(why);}
 String hex(byte[] raw){StringBuilder out=new StringBuilder();for(byte v:raw)out.append(String.format("%02x",v&255));return out.toString();}
 Map<String,Object> function(Function f){Map<String,Object> r=new LinkedHashMap<>();if(f==null)return r;r.put("entry",f.getEntryPoint().toString());r.put("name",f.getName());r.put("body",f.getBody().toString());r.put("signature_inferred",f.getSignature().toString());r.put("signature_source",f.getSignatureSource().toString());return r;}
 public void run() throws Exception {
  String[] args=getScriptArgs();require(args.length==3,"mode manifest output required");String mode=args[0];require(Set.of("inspect","apply","verify").contains(mode),"invalid mode");
  JsonObject plan=JsonParser.parseString(Files.readString(Path.of(args[1]))).getAsJsonObject();Path out=Path.of(args[2]);
  require(currentProgram.getExecutableSHA256().equals(plan.get("sha256").getAsString()),"firmware SHA");
  require(currentProgram.getLanguageID().toString().equals("ARM:LE:32:v8"),"language");require(currentProgram.getCompilerSpec().getCompilerSpecID().toString().equals("default"),"compiler");require(currentProgram.getImageBase().getOffset()==0x8000,"image base");
  Map<String,Object> result=new LinkedHashMap<>();List<Map<String,Object>> points=new ArrayList<>();int byteChecks=0;
  for(JsonElement element:plan.getAsJsonArray("baseline_functions")){JsonObject expected=element.getAsJsonObject();Function f=getFunctionAt(toAddr(Long.parseLong(expected.get("entry").getAsString(),16)));require(new Gson().toJsonTree(function(f)).equals(expected),"baseline function drift "+expected.get("entry"));}
  Map<Long,Map<String,Object>> retained=new LinkedHashMap<>();
  for(JsonElement element:plan.getAsJsonArray("points")){Address address=toAddr(Long.decode(element.getAsJsonObject().get("address").getAsString()));Function f=getFunctionContaining(address);if(f!=null)retained.put(f.getEntryPoint().getOffset(),function(f));}
  List<Map<String,Object>> displayFunctions=new ArrayList<>();
  for(JsonElement element:plan.getAsJsonArray("display_functions")){JsonObject row=element.getAsJsonObject();Function f=getFunctionAt(toAddr(Long.parseLong(row.get("entry").getAsString(),16)));require(f!=null,"display entry "+row);require(f.getName().equals(row.get("name").getAsString())&&f.getBody().toString().equals(row.get("body").getAsString()),"display metadata "+row);displayFunctions.add(function(f));retained.put(f.getEntryPoint().getOffset(),function(f));}
  for(long a:new long[]{0xb3ac4,0x571d24,0x69850c,0x69afc0}){Function f=getFunctionAt(toAddr(a));require(f!=null,"startup entry");retained.put(a,function(f));}
  AddressSet rangeBody=new AddressSet(toAddr(0x1c79d0),toAddr(0x1c7a37));
  for(JsonElement element:plan.getAsJsonArray("range_instructions")){JsonObject row=element.getAsJsonObject();Address address=toAddr(Long.decode(row.get("address").getAsString()));byte[] raw=new byte[4];currentProgram.getMemory().getBytes(address,raw);require(hex(raw).equals(row.get("bytes").getAsString()),"range bytes "+address);require(BigInteger.ZERO.equals(currentProgram.getProgramContext().getValue(currentProgram.getRegister("TMode"),address,false)),"range ARM mode");Function f=getFunctionContaining(address);require(f==null||f.getEntryPoint().equals(toAddr(0x1c79d0)),"unexpected range owner "+function(f));}
  int tx=mode.equals("apply")?currentProgram.startTransaction("SP16 accepted Send batch integration"):-1;boolean commit=false;
  try {
  for(JsonElement element:plan.getAsJsonArray("points")){
   JsonObject row=element.getAsJsonObject();Address address=toAddr(Long.decode(row.get("address").getAsString()));
   if(row.has("bytes")){String expected=row.get("bytes").getAsString();byte[] raw=new byte[expected.length()/2];currentProgram.getMemory().getBytes(address,raw);require(hex(raw).equals(expected),"bytes "+address);byteChecks++;}
   if(row.get("kind").getAsString().equals("instruction"))require(BigInteger.ZERO.equals(currentProgram.getProgramContext().getValue(currentProgram.getRegister("TMode"),address,false)),"ARM mode "+address);
   String name=row.get("label").getAsString();String note="[SP16 Send batch 2026-10-09] "+row.get("comment").getAsString()+" Evidence: "+row.get("source").getAsString();
   boolean named=false;for(Bookmark bookmark:currentProgram.getBookmarkManager().getBookmarks(address,"Note"))if(bookmark.getCategory().equals("SP16 Send batch")&&bookmark.getComment().equals(name))named=true;
   String old=currentProgram.getListing().getComment(CodeUnit.EOL_COMMENT,address);
   if(mode.equals("apply")){
    if(!named)currentProgram.getBookmarkManager().setBookmark(address,"Note","SP16 Send batch",name);
    if(old==null || !old.contains(note))currentProgram.getListing().setComment(address,CodeUnit.EOL_COMMENT,(old==null||old.isEmpty()?"":old+"\n")+note);
   }
   if(mode.equals("verify")){
    require(named,"bookmark "+name);require(old!=null&&old.contains(note),"comment "+address);
   }
   Map<String,Object> item=new LinkedHashMap<>();item.put("address",address.toString());item.put("at",function(getFunctionAt(address)));item.put("containing",function(getFunctionContaining(address)));item.put("bookmark",name);points.add(item);
  }
  Map<String,Object> rangeBefore=function(getFunctionAt(toAddr(0x1c79d0)));Map<String,Object> fragmentBefore=function(getFunctionAt(toAddr(0x1c7a1c)));
  if(plan.get("repair_range").getAsBoolean()&&mode.equals("apply")){
   require(getFunctionAt(toAddr(0x1c7a1c))==null,"unexpected separate fragment; preserve for manual reconciliation");
   DisassembleCommand command=new DisassembleCommand(toAddr(0x1c79d0),rangeBody,true);require(command.applyTo(currentProgram,monitor),"range disassembly: "+command.getStatusMsg());
   Function range=getFunctionAt(toAddr(0x1c79d0));
   if(range==null)range=currentProgram.getFunctionManager().createFunction("sp16_batch_send_ui_range_selector",toAddr(0x1c79d0),rangeBody,SourceType.USER_DEFINED);
   else require(range.getBody().equals(rangeBody),"unexpected existing range body; no destructive repair");
   require(range!=null,"range creation");
  }
  if(!mode.equals("inspect")&&plan.get("repair_range").getAsBoolean()){
   require(getFunctionAt(toAddr(0x1c7a1c))==null,"range fragment absent");Function range=getFunctionAt(toAddr(0x1c79d0));require(range!=null&&range.getBody().getNumAddresses()==104&&range.getBody().getMaxAddress().equals(toAddr(0x1c7a37)),"range body");
  }
  List<String> types=new ArrayList<>();CategoryPath category=new CategoryPath(CATEGORY);
  for(JsonElement element:plan.getAsJsonArray("types")){
   JsonObject row=element.getAsJsonObject();String name=row.get("name").getAsString();DataType existing=currentProgram.getDataTypeManager().getDataType(category,name);
   if(mode.equals("apply")&&existing==null){
    StructureDataType type=new StructureDataType(category,name,row.get("size").getAsInt());type.setDescription("Partial static offset view; not a recovered C++ class/prototype; unknown bytes retained. Batch evidence manifest.");
    for(JsonElement field:row.getAsJsonArray("fields")){
     JsonObject f=field.getAsJsonObject();String kind=f.get("type").getAsString();DataType dt=kind.equals("byte")?ByteDataType.dataType:kind.equals("short")?ShortDataType.dataType:kind.equals("int")?IntegerDataType.dataType:UnsignedIntegerDataType.dataType;
     type.replaceAtOffset(f.get("offset").getAsInt(),dt,dt.getLength(),f.get("name").getAsString(),"Original offset; pointer fields are raw ARM32 words.");
    }
    existing=currentProgram.getDataTypeManager().addDataType(type,DataTypeConflictHandler.DEFAULT_HANDLER);
   }
   if(!mode.equals("inspect")){
    require(existing instanceof Structure,"saved partial type "+name);Structure s=(Structure)existing;require(s.getLength()==row.get("size").getAsInt(),"type size "+name);
    for(JsonElement field:row.getAsJsonArray("fields")){JsonObject f=field.getAsJsonObject();DataTypeComponent c=s.getComponentAt(f.get("offset").getAsInt());require(c!=null&&f.get("name").getAsString().equals(c.getFieldName()),"field "+name+" "+f);}
   }
   types.add(name);
  }
  // Preserve startup proof and its inferred prototypes/continuation boundaries.
  for(long a:new long[]{0xb3ac4,0x571d24,0x69850c,0x69afc0})require(getFunctionAt(toAddr(a))!=null,"startup entry "+Long.toHexString(a));
  require(getFunctionAt(toAddr(0x698548))==null&&getFunctionAt(toAddr(0xb4060))==null,"startup continuations not entries");
  if(!mode.equals("inspect"))for(JsonElement element:plan.getAsJsonArray("range_instructions")){Address address=toAddr(Long.decode(element.getAsJsonObject().get("address").getAsString()));Instruction ins=getInstructionAt(address);require(ins!=null&&ins.getLength()==4,"range instruction "+address);}
  for(Map.Entry<Long,Map<String,Object>> item:retained.entrySet())require(function(getFunctionAt(toAddr(item.getKey()))).equals(item.getValue()),"existing function changed "+Long.toHexString(item.getKey()));
  result.put("range_after",function(getFunctionAt(toAddr(0x1c79d0))));result.put("range_instruction_checks",plan.getAsJsonArray("range_instructions").size());result.put("display_functions",displayFunctions);result.put("existing_function_metadata_preserved",retained.size());
  result.put("passed",true);result.put("mode",mode);result.put("program",currentProgram.getName());result.put("sha256",currentProgram.getExecutableSHA256());result.put("language",currentProgram.getLanguageID().toString());result.put("compiler",currentProgram.getCompilerSpec().getCompilerSpecID().toString());result.put("image_base",currentProgram.getImageBase().toString());result.put("byte_checks",byteChecks);result.put("points",points);result.put("range_before",rangeBefore);result.put("fragment_before",fragmentBefore);result.put("partial_types",types);result.put("range_repair_requested",plan.get("repair_range").getAsBoolean());result.put("autoanalysis",false);result.put("firmware_executed",false);
  commit=true;
  } finally { if(tx!=-1)currentProgram.endTransaction(tx,commit); }
  Files.writeString(out,new GsonBuilder().setPrettyPrinting().create().toJson(result)+"\n");println("SP16_SEND_BATCH_"+mode.toUpperCase()+"_PASSED");
 }
}
