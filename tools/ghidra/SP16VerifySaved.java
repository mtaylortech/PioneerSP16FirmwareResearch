// ---------------------------------------------------------------------------
// SP-16 open research — original research Ghidra script, unchanged below.
// Ghidra script that reopens a saved program read-only and verifies annotations.
// Original path: ghidra/scripts/SP16VerifySaved.java
// Original SHA-256: 3fd0eaf4c062344ecc689bfc816c4b1fdac86d47c42708dc148198ba8ec6c7fb
// License: MIT (see repository LICENSE). Addresses refer to the firmware
// version named in the script/docs; they are wrong for other versions.
// ---------------------------------------------------------------------------
// Reopen the saved program read-only and verify boundaries, annotations and selected bytes.
//@category PioneerSP16
import java.nio.file.*;
import java.util.*;
import java.math.BigInteger;
import com.google.gson.*;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.data.*;
import ghidra.framework.options.Options;
public class SP16VerifySaved extends GhidraScript {
    void check(boolean ok,String text){if(!ok)throw new IllegalStateException(text);}
    public void run()throws Exception {
        Path out=Path.of(getScriptArgs()[0]);Path root=out.getParent().getParent().getParent();
        Gson g=new GsonBuilder().setPrettyPrinting().create();Map<String,Object> result=new LinkedHashMap<>();
        check(currentProgram.getDomainFile().getName().equals("EP085_Main_R_fw160"),"Program name");
        check(currentProgram.getExecutableSHA256().equals("3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464"),"SHA");
        JsonObject map=JsonParser.parseString(Files.readString(root.resolve("experiments/audit-remediation-20261009/lifecycle/overlay/lifecycle-map.json"))).getAsJsonObject();
        int count=0;
        for(Map.Entry<String,JsonElement> e:map.getAsJsonObject("points").entrySet()){
            long a=Long.decode(e.getKey());String expected=e.getValue().getAsString();byte[] b=new byte[expected.length()/2];currentProgram.getMemory().getBytes(toAddr(a),b);
            StringBuilder hex=new StringBuilder();for(byte v:b)hex.append(String.format("%02x",v&255));check(hex.toString().equals(expected),"Byte mismatch "+e.getKey());count++;
        }
        Map<String,Object> entries=new LinkedHashMap<>();
        for(long a:new long[]{0xb3ac4,0x571d24,0x69850c,0x69afc0}){
            Function f=getFunctionAt(toAddr(a));check(f!=null,"Entry "+toAddr(a));
            check(BigInteger.ZERO.equals(currentProgram.getProgramContext().getValue(currentProgram.getRegister("TMode"),toAddr(a),false)),"ARM context");
            entries.put(toAddr(a).toString(),f.getSignature().toString());
        }
        for(long a:new long[]{0x698548,0xb4060})check(getFunctionAt(toAddr(a))==null,"Continuation incorrectly made function");
        check(getFunctionContaining(toAddr(0x698548)).getEntryPoint().equals(toAddr(0x69850c)),"Inner continuation owner");
        check(getFunctionContaining(toAddr(0xb4060)).getEntryPoint().equals(toAddr(0xb4034)),"Outer continuation owner");
        check(getInstructionAt(toAddr(0x57222c)).getMnemonicString().equals("ldmia"),"Normal return instruction");
        for(String name:new String[]{"LiveSamplerApplication_view_009327f0","MessageManager_view_0069826c","MessageQueue_view_00697fc0"})check(currentProgram.getDataTypeManager().getDataType(new CategoryPath("/SP16_Static_Views"),name)!=null,"Saved type "+name);
        for(long a:new long[]{0x102e8,0x113f8,0x10a5c})check(!getFunctionAt(toAddr(a)).hasNoReturn(),"Incorrect PLT no-return "+toAddr(a));
        Map<String,Object> options=new TreeMap<>();Options opts=currentProgram.getOptions(Program.ANALYSIS_PROPERTIES);for(String k:opts.getOptionNames())options.put(k,String.valueOf(opts.getObject(k,null)));
        result.put("passed",true);result.put("mapped_byte_pairs",count);result.put("entries_and_analyst_signatures",entries);result.put("continuations_not_entries",new String[]{"00698548","000b4060"});result.put("saved_partial_types",3);result.put("language",currentProgram.getLanguageID().toString());result.put("compiler",currentProgram.getCompilerSpec().getCompilerSpecID().toString());result.put("analysis_options_saved",options);result.put("firmware_executed",false);
        Files.writeString(out.resolve("saved-project-verification.json"),g.toJson(result)+"\n");println("SAVED_PROJECT_VERIFIED byte_pairs="+count);
    }
}
