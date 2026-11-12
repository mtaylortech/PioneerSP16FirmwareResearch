// ---------------------------------------------------------------------------
// SP-16 open research — original research Ghidra script, unchanged below.
// Ghidra script used for the 1.30->1.31 cross-version function-correspondence pilot (seed functions).
// Original path: firmware/tools/ghidra/SP16CorpusSeeds.java
// Original SHA-256: fbe0f933666c6f097391ecbc7737e362238d9dc08e76c97a1c8263825bc9e794
// License: MIT (see repository LICENSE). Addresses refer to the firmware
// version named in the script/docs; they are wrong for other versions.
// ---------------------------------------------------------------------------
//@category PioneerSP16
import java.nio.file.*;
import java.util.*;
import com.google.gson.GsonBuilder;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.lang.Register;
public class SP16CorpusSeeds extends GhidraScript {
 public void run() throws Exception {
  String[] args=getScriptArgs();
  for(int n=1;n<args.length;n++) {
   Address a=toAddr(args[n]); disassemble(a);
   Function f=getFunctionAt(a); if(f==null) f=createFunction(a,null);
   if(f==null) throw new IllegalStateException("Seed not function: "+a);
  }
  Map<String,Object> result=new LinkedHashMap<>();
  result.put("original_elf_sha256",currentProgram.getExecutableSHA256());
  result.put("language",currentProgram.getLanguageID().toString());
  result.put("compiler",currentProgram.getCompilerSpec().getCompilerSpecID().toString());
  result.put("image_base",currentProgram.getImageBase().toString());
  result.put("profile","ELF default relocations; ARM:LE:32:v8/default; no global analysis; focused disassembly");
  result.put("program",currentProgram.getDomainFile().getPathname());
  List<Object> fs=new ArrayList<>();
  for(int n=1;n<args.length;n++) {
   Address a=toAddr(args[n]); Function f=getFunctionAt(a); Map<String,Object> row=new LinkedHashMap<>();
   row.put("entry",a.toString()); row.put("name",f.getName());
   Register tm=currentProgram.getRegister("TMode");
   row.put("TMode",tm==null?null:currentProgram.getProgramContext().getValue(tm,a,false));
   row.put("body",f.getBody().toString());row.put("body_bytes",f.getBody().getNumAddresses());
   List<Object> ins=new ArrayList<>();
   InstructionIterator it=currentProgram.getListing().getInstructions(f.getBody(),true);
   while(it.hasNext()) {
    Instruction i=it.next(); Map<String,Object> ir=new LinkedHashMap<>();
    ir.put("address",i.getAddress().toString());ir.put("text",i.toString());
    StringBuilder hex=new StringBuilder(); for(byte b:i.getBytes()) hex.append(String.format("%02x",b&255));
    ir.put("bytes",hex.toString());ir.put("flows",Arrays.stream(i.getFlows()).map(Object::toString).toArray());
    ins.add(ir);
   }
   row.put("instructions",ins);fs.add(row);
  }
  result.put("functions",fs);
  Files.writeString(Path.of(args[0]),new GsonBuilder().setPrettyPrinting().create().toJson(result)+"\n");
  println("CORPUS_SEEDS_EXPORTED "+fs.size());
 }
}
