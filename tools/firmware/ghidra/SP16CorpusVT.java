// ---------------------------------------------------------------------------
// SP-16 open research — original research Ghidra script, unchanged below.
// Ghidra script that ran Version Tracking correlators for the 1.30->1.31 pilot without applying markup.
// Original path: firmware/tools/ghidra/SP16CorpusVT.java
// Original SHA-256: b33bcc09c5c27ba1a8aefadddaadcb0f84179a5531e61136f7aa4dc1c29d573f
// License: MIT (see repository LICENSE). Addresses refer to the firmware
// version named in the script/docs; they are wrong for other versions.
// ---------------------------------------------------------------------------
//@category PioneerSP16
import java.nio.file.*;
import java.util.*;
import com.google.gson.GsonBuilder;
import ghidra.app.script.GhidraScript;
import ghidra.framework.model.DomainFile;
import ghidra.program.model.listing.Program;
import ghidra.program.model.address.*;
import ghidra.feature.vt.api.correlator.program.*;
import ghidra.feature.vt.api.db.VTSessionDB;
import ghidra.feature.vt.api.main.*;
import ghidra.feature.vt.api.util.*;
public class SP16CorpusVT extends GhidraScript {
 public void run() throws Exception {
  String[] args=getScriptArgs();Program source=null;VTSessionDB session=null;
  try {
   DomainFile file=state.getProject().getProjectData().getRootFolder().getFile(args[0]);
   if(file==null) throw new IllegalStateException("Missing source "+args[0]);
   source=(Program)file.getDomainObject(this,false,false,monitor);
   end(true); // Required by installed AutoVersionTrackingScript before synchronized locks.
   session=new VTSessionDB("SP16_130_131_reader_pilot",source,currentProgram,this);
   int tx=session.startTransaction("Non-applying focused correlators");
   List<Object> matches=new ArrayList<>();
   try {
    AddressSet src=new AddressSet(),dst=new AddressSet();
    for(int n=2;n<args.length;n++) {
     Address a=source.getAddressFactory().getDefaultAddressSpace().getAddress(args[n]);
     src.add(source.getFunctionManager().getFunctionAt(a).getBody());
     Address b=toAddr(args[n]);dst.add(getFunctionAt(b).getBody());
    }
    VTProgramCorrelatorFactory[] factories={new ExactMatchBytesProgramCorrelatorFactory(),new ExactMatchInstructionsProgramCorrelatorFactory()};
    for(VTProgramCorrelatorFactory factory:factories) {
     VTProgramCorrelator correlator=factory.createCorrelator(source,src,currentProgram,dst,factory.createDefaultOptions());
     VTMatchSet set=correlator.correlate(session,monitor);
     for(VTMatch m:set.getMatches()) {
      Map<String,Object> r=new LinkedHashMap<>();r.put("method",factory.getName());
      r.put("source_address",m.getSourceAddress().toString());r.put("destination_address",m.getDestinationAddress().toString());
      r.put("similarity",m.getSimilarityScore().toString());r.put("confidence_score",m.getConfidenceScore().toString());
      r.put("association_status",m.getAssociation().getStatus().toString());matches.add(r);
     }
    }
   } finally { session.endTransaction(tx,true); }
   Map<String,Object> result=new LinkedHashMap<>();
   result.put("source_sha256",source.getExecutableSHA256());result.put("destination_sha256",currentProgram.getExecutableSHA256());
   result.put("matches",matches);result.put("markup_applied",false);
   state.getProject().getProjectData().getRootFolder().createFile("SP16_130_131_reader_pilot",session,monitor);
   Files.writeString(Path.of(args[1]),new GsonBuilder().setPrettyPrinting().create().toJson(result)+"\n");
   println("CORPUS_VT_EXPORTED "+matches.size());
  } finally {if(session!=null)session.release(this);if(source!=null)source.release(this);}
 }
}
