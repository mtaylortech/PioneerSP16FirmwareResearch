// ---------------------------------------------------------------------------
// SP-16 open research — original research Ghidra script, unchanged below.
// Ghidra headless script: focused static decompilation/export of the 1.60 startup chain.
// Original path: ghidra/scripts/SP16FocusedStartup.java
// Original SHA-256: c8d743b515da824cef3b4452b287bf4ce62fdb334b4477ea9f81cfcd14fb18a2
// License: MIT (see repository LICENSE). Addresses refer to the firmware
// version named in the script/docs; they are wrong for other versions.
// ---------------------------------------------------------------------------
// Focused static startup research. Does not execute firmware or load a runtime.
//@category PioneerSP16
import java.nio.file.*;
import java.util.*;
import java.math.BigInteger;
import com.google.gson.*;
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.framework.Application;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.symbol.*;

public class SP16FocusedStartup extends GhidraScript {
    Path out; Gson gson=new GsonBuilder().setPrettyPrinting().create();
    void write(String n,String s)throws Exception{Files.writeString(out.resolve(n),s);}
    String hex(byte[] b){StringBuilder s=new StringBuilder();for(byte v:b)s.append(String.format("%02x",v&255));return s.toString();}
    String ascii(Address a){
        try {
            MemoryBlock block=currentProgram.getMemory().getBlock(a);
            if(block==null || block.isExecute())return null;
            StringBuilder s=new StringBuilder();
            for(int i=0;i<256;i++){
                int v=currentProgram.getMemory().getByte(a.add(i))&255;
                if(v==0)return s.length()>=3?s.toString():null;
                if(v<32 || v>126)return null;s.append((char)v);
            }
        }catch(Exception ignored){}return null;
    }
    Map<String,Object> ref(Reference r){
        Map<String,Object> x=new LinkedHashMap<>();x.put("from",r.getFromAddress().toString());x.put("to",r.getToAddress().toString());x.put("type",r.getReferenceType().toString());
        Function f=getFunctionContaining(r.getFromAddress());x.put("owner",f==null?null:f.getEntryPoint().toString());
        Symbol s=getSymbolAt(r.getToAddress());x.put("symbol",s==null?null:s.getName(true));return x;
    }
    protected long[] selectedStarts(){return new long[]{0xb3ac4,0xb4034,0x56e7bc,0x571d24,0x69850c,0x7552b0,0x69afc0,
            0x5712cc,0x57155c,0x56f7f4,0x56c4bc,0x56cd14,0x56cfe4,0x55659c,0x65e09c,
            0x37c428,0x37fd38,0x523514,0x56e8ec,0x697fc0,0x696e68,0x69826c,0x6457dc};}
    public void run()throws Exception{
        String[] args=getScriptArgs();out=Path.of(args[0]);Files.createDirectories(out);
        if(!currentProgram.getExecutableSHA256().equals("3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464"))throw new IllegalStateException("Wrong firmware identity");
        if(getFunctionAt(toAddr(0x56e8ec))==null){disassemble(toAddr(0x56e8ec));createFunction(toAddr(0x56e8ec),"sp16_preinit_true_0056e8ec");}
        long[] starts=selectedStarts();
        DecompInterface d=new DecompInterface();List<Map<String,Object>> all=new ArrayList<>();long begun=System.nanoTime();
        try {
            if(!d.openProgram(currentProgram))throw new IllegalStateException(d.getLastMessage());
            for(long a:starts){
                if((System.nanoTime()-begun)/1000000000L>540){println("FOCUSED_STATIC_LIMIT partial exports retained");break;}
                monitor.checkCancelled();Function f=getFunctionAt(toAddr(a));
                if(f==null){println("No entry at "+toAddr(a));continue;}
                String id=f.getEntryPoint().toString();StringBuilder asm=new StringBuilder("STATIC ORIGINAL INSTRUCTIONS; "+id+" "+f.getName()+"\n");
                List<Map<String,Object>> calls=new ArrayList<>(),strings=new ArrayList<>(),incoming=new ArrayList<>();Set<String> seen=new HashSet<>();
                for(Instruction i:currentProgram.getListing().getInstructions(f.getBody(),true)){
                    asm.append(i.getAddress()).append(": ").append(hex(i.getBytes())).append(" ").append(i).append("\n");
                    for(Reference r:i.getReferencesFrom()){
                        if(r.getReferenceType().isCall())calls.add(ref(r));
                        if(r.getReferenceType().isData()){
                            Address base=r.getToAddress();List<Address> candidates=new ArrayList<>();candidates.add(base);
                            try{candidates.add(toAddr(Integer.toUnsignedLong(currentProgram.getMemory().getInt(base))));}catch(Exception ignored){}
                            for(Address target:candidates){String s=ascii(target);if(s!=null && seen.add(i.getAddress()+":"+target)){
                                Map<String,Object> item=new LinkedHashMap<>();item.put("instruction",i.getAddress().toString());item.put("reference",base.toString());item.put("string_address",target.toString());item.put("string",s);strings.add(item);
                            }}
                        }
                    }
                }
                ReferenceIterator refs=currentProgram.getReferenceManager().getReferencesTo(f.getEntryPoint());while(refs.hasNext())incoming.add(ref(refs.next()));
                DecompileResults dr=d.decompileFunction(f,45,monitor);
                Map<String,Object> row=new LinkedHashMap<>();row.put("entry",id);row.put("name_inferred",f.getName());row.put("body",f.getBody().toString());
                row.put("signature_inferred",f.getSignature().toString());row.put("decompile_completed",dr.decompileCompleted());row.put("error",dr.getErrorMessage());row.put("direct_calls",calls);row.put("incoming_references",incoming);row.put("strings",strings);
                BigInteger mode=currentProgram.getProgramContext().getValue(currentProgram.getRegister("TMode"),f.getEntryPoint(),false);row.put("TMode",mode==null?null:mode.toString());
                write(id+".asm.txt",asm.toString());write(id+".inferred.c","/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */\n"+(dr.decompileCompleted()?dr.getDecompiledFunction().getC():"// PARTIAL: "+dr.getErrorMessage()));
                write(id+".json",gson.toJson(row)+"\n");all.add(row);write("index.json",gson.toJson(all)+"\n");println("FOCUS "+id+" complete="+dr.decompileCompleted()+" strings="+strings.size());
            }
            Map<String,Object> info=new LinkedHashMap<>();info.put("version",Application.getApplicationVersion());info.put("sha256",currentProgram.getExecutableSHA256());info.put("language",currentProgram.getLanguageID().toString());info.put("compiler",currentProgram.getCompilerSpec().getCompilerSpecID().toString());info.put("image_base",currentProgram.getImageBase().toString());info.put("autoanalysis","Reused saved corrected ELF project; -noanalysis");info.put("decompile_limit_seconds",45);info.put("script_limit_seconds",540);info.put("export_count",all.size());info.put("firmware_executed",false);write("metadata.json",gson.toJson(info)+"\n");
            println("FOCUSED_STATIC_EXPORT_SAVED program="+currentProgram.getDomainFile().getPathname());
        }finally{d.dispose();}
    }
}
