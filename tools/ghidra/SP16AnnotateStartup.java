// ---------------------------------------------------------------------------
// SP-16 open research — original research Ghidra script, unchanged below.
// Ghidra script that applied the reviewed startup annotations (names, comments, partial structures) to the 1.60 program. See symbols/ for the portable result.
// Original path: ghidra/scripts/SP16AnnotateStartup.java
// Original SHA-256: d9454bacf3c4b5100db69d26977fad432f2409ed892072d23f0b84408a6469db
// License: MIT (see repository LICENSE). Addresses refer to the firmware
// version named in the script/docs; they are wrong for other versions.
// ---------------------------------------------------------------------------
// Analyst annotations: original instructions unchanged. Types are partial evidence views.
//@category PioneerSP16
import java.util.*;
import java.nio.file.*;
import ghidra.program.model.data.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;

public class SP16AnnotateStartup extends SP16FocusedStartup {
    List<Map<String,Object>> changes=new ArrayList<>();
    DataType ptr(DataType t){return new PointerDataType(t,4,currentProgram.getDataTypeManager());}
    Structure structure(String name,int size,Object[][] fields){
        StructureDataType s=new StructureDataType(new CategoryPath("/SP16_Static_Views"),name,size);
        for(Object[] f:fields)s.replaceAtOffset((int)f[0],(DataType)f[1],((DataType)f[1]).getLength(),(String)f[2],(String)f[3]);
        return (Structure)currentProgram.getDataTypeManager().addDataType(s,DataTypeConflictHandler.REPLACE_HANDLER);
    }
    void annotate(long a,String name,String explanation,DataType ret,DataType[] args,String[] names)throws Exception {
        Function f=getFunctionAt(toAddr(a));if(f==null)throw new IllegalStateException("Missing function "+toAddr(a));
        f.setName(name+"_"+f.getEntryPoint(),SourceType.USER_DEFINED);
        f.setComment("SUPPORTED ANALYST INTERPRETATION; address identity retained. "+explanation+" Original source signature is not recovered.");
        if(ret!=null){
            f.setReturnType(ret,SourceType.USER_DEFINED);
            List<Variable> p=new ArrayList<>();for(int i=0;i<args.length;i++)p.add(new ParameterImpl(names[i],args[i],currentProgram));
            f.replaceParameters(p,Function.FunctionUpdateType.DYNAMIC_STORAGE_ALL_PARAMS,true,SourceType.USER_DEFINED);
        }
        Map<String,Object> row=new LinkedHashMap<>();row.put("address",f.getEntryPoint().toString());row.put("name",f.getName());row.put("rationale",explanation);row.put("signature_is_analyst_convention",ret!=null);changes.add(row);
    }
    @Override protected long[] selectedStarts(){return new long[]{0xb3ac4,0xb4034,0x56e7bc,0x56e8ec,0x571d24,0x69850c,0x7552b0,0x69afc0,0x5712cc,0x57155c,0x56f7f4,0x56c4bc,0x56cd14,0x56cfe4,0x55659c,0x65e09c,0x65d7c0,0x37c428,0x37fd38,0x523514,0x697fc0,0x696e68,0x69826c,0x6457dc,0x69653c,0x64703c,0x69ac58};}
    @Override public void run()throws Exception {
        if(!currentProgram.getExecutableSHA256().equals("3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464"))throw new IllegalStateException("Wrong identity");
        DataType u32=UnsignedIntegerDataType.dataType,u8=ByteDataType.dataType,voidT=VoidDataType.dataType,pvoid=ptr(voidT);
        Structure app=structure("LiveSamplerApplication_view_009327f0",0x8c,new Object[][]{
            {0,pvoid,"primary_vtable","RTTI LiveSamplerApplication at 00932990; vtable address point 009327f0"},
            {4,u32,"exit_code","Read by main after dispatch"},{8,u8,"initialise_wrapper_state","Cleared at 00698558"},
            {0xc,pvoid,"optional_listener","Sorted registration through 00696e68"},{0x10,pvoid,"secondary_vtable","Factory store"},
            {0x18,pvoid,"main_window","MainWindow RTTI and store 0057217c"},{0x1c,pvoid,"settings","Settings constructor 0056c4bc; store 00571d90"},
            {0x28,pvoid,"ui_thread","UIThread RTTI; allocation 0x418"},{0x2c,pvoid,"processing_graph","Mode-dependent construction by 005712cc"},
            {0x40,pvoid,"controller_data_manager","ControllerDataManager RTTI in default UI constructor"}});
        Structure mgr=structure("MessageManager_view_0069826c",0x28,new Object[][]{
            {4,u8,"initialise_gate","Read by initialise wrapper; semantic purpose unresolved"},
            {5,u8,"dispatch_exit_flag","Tested at 0069b04c"},{8,u32,"owner_thread","pthread_self in constructor"},
            {0x10,new ArrayDataType(u8,24,1),"mutex_storage","pthread_mutex_init target"}});
        Structure queue=structure("MessageQueue_view_00697fc0",0x34,new Object[][]{
            {0,new ArrayDataType(u8,24,1),"mutex_storage","pthread mutex"},{0x18,pvoid,"message_array","Queue storage"},
            {0x1c,u32,"capacity","Array allocation capacity"},{0x20,u32,"count","Locked append/pop"},
            {0x24,u32,"wake_write_fd","socketpair fd[0]"},{0x28,u32,"wake_read_fd","socketpair fd[1]; select source"},
            {0x2c,u32,"wake_count","Byte wake bookkeeping"},{0x30,u32,"alternation_counter","Chooses queue/X11 servicing order"}});
        DataType appP=ptr(app),mgrP=ptr(mgr);
        annotate(0x571d24,"sp16_initialise","Constructs settings, UIThread, mode graph and MainWindow. Normal return 0057222c; caller ignores r0, so void is a working convention.",voidT,new DataType[]{appP,pvoid},new String[]{"app","startup_context"});
        annotate(0x69850c,"juce_initialise_wrapper","Indirect +0x14 call returns at 00698548; manager gate controls 0/1 result.",u32,new DataType[]{appP},new String[]{"app"});
        annotate(0x56e7bc,"sp16_application_factory","Allocation 0x8c, original LiveSamplerApplication vtable.",appP,new DataType[]{},new String[]{});
        annotate(0x56e8ec,"sp16_preinit_true","ARM mov r0,#1; bx lr.",u32,new DataType[]{appP},new String[]{"app"});
        annotate(0x69afc0,"juce_x11_message_dispatch","XPending/XNextEvent and mutex-protected internal virtual callbacks, select wait, exit flag +5.",voidT,new DataType[]{mgrP},new String[]{"manager"});
        annotate(0x69826c,"juce_get_message_manager","Singleton construction, Message Thread and pthread_self.",mgrP,new DataType[]{},new String[]{});
        annotate(0x5712cc,"sp16_build_mode_graph","Mode bit 0 selects test graph; bits 1/2 skip normal graph. Audio/MIDI node strings support interpretation.",voidT,new DataType[]{appP,u32},new String[]{"app","mode_flags"});
        annotate(0x57155c,"sp16_wire_graph_controllers","Mode/graph-dependent helper objects; relationships inferred.",voidT,new DataType[]{appP,u32},new String[]{"app","mode_flags"});
        annotate(0x56f7f4,"sp16_create_mode_content","Mode-dependent view; default ControllerDataManager RTTI survives.",pvoid,new DataType[]{appP,u32},new String[]{"app","mode_flags"});
        long[] others={0xb3ac4,0xb4034,0x7552b0,0x56c4bc,0x56cd14,0x56cfe4,0x55659c,0x65e09c,0x37c428,0x697fc0,0x696e68,0x6457dc};
        String[] n={"main_factory_setup","main_initialise_then_dispatch","sp16_initialise_thunk","Settings_construct","UIThread_construct","UIThread_start","sp16_device_initialise","sp16_mode_tokens_construct","TSP16VirtualPathSetting_renameToraiz","juce_x11_queue_bootstrap","juce_register_listener_sorted","sleep_milliseconds"};
        String[] why={"Main entry stores factory then transfers to main body.","vtable +0x30 call, return at 000b4060, nonzero branch to dispatch call 000b4094.","Tail branch to 0069850c.","Original diagnostic Settings::Settings(), Toraiz_SP16.dat and FlashWriter.","Original UIThread/UIThreadTimer strings and RTTI.","Thread start and singleton binding; no completion proof.","Called with testmode flag; hardware effects unverified.","Token checks testmode/mscmode/colmode/scriptmode/scriptrecmode.","Original full method diagnostic string survives.","X11 imports, DISPLAY, socketpair, auxiliary window.","Mutex-protected sorted pointer insertion.","Converts milliseconds and calls nanosleep."};
        for(int i=0;i<others.length;i++)annotate(others[i],n[i],why[i],null,null,null);
        annotate(0x56c4bc,"Settings_construct","r0 saved as this at 0056c4c0 and returned at 0056c558; r1 is settings path, r2 is forwarded into base constructor. Surviving Settings::Settings() diagnostic.",pvoid,new DataType[]{pvoid,ptr(CharDataType.dataType),ptr(CharDataType.dataType)},new String[]{"settings","path","settings_label"});
        annotate(0x56cd14,"UIThread_construct","r0 is constructor destination; original UIThread/UIThreadTimer strings and RTTI.",pvoid,new DataType[]{pvoid},new String[]{"thread"});
        annotate(0x56cfe4,"UIThread_start","Tail branch to 0064703c after optional stop request; thread startup does not establish worker completion.",voidT,new DataType[]{pvoid},new String[]{"thread"});
        annotate(0x64703c,"juce_start_thread","r0 supplies thread object; pthread_create at 0064708c and detach on zero return.",voidT,new DataType[]{pvoid},new String[]{"thread"});
        annotate(0x6457dc,"sleep_milliseconds","Integer milliseconds converted to timespec; nanosleep result ignored.",voidT,new DataType[]{IntegerDataType.dataType},new String[]{"milliseconds"});
        createLabel(toAddr(0x9327f0),"LiveSamplerApplication_vtable_009327f0",true,SourceType.USER_DEFINED);
        setEOLComment(toAddr(0x698548),"RETURN CONTINUATION of indirect initializer call; not function entry or runtime receipt.");
        setEOLComment(toAddr(0xb4060),"RETURN CONTINUATION of wrapper call. Nonzero r0 branches toward dispatch.");
        setEOLComment(toAddr(0x571f5c),"Poll exhaustion falls through to normal setup; no failure return here.");
        setEOLComment(toAddr(0x5721e0),"statvfs return status not checked on this path; low-space interpretation provisional.");
        Path dest=Path.of(getScriptArgs()[0]);Files.createDirectories(dest);
        Files.writeString(dest.resolve("annotations.json"),gson.toJson(changes)+"\n");
        StringBuilder schema=new StringBuilder("Partial analyst views. Unknown offsets remain undefined; not recovered source layouts.\n");
        for(Structure s:new Structure[]{app,mgr,queue}){
            schema.append(s.getName()).append(" size=0x").append(Integer.toHexString(s.getLength())).append("\n");
            for(DataTypeComponent c:s.getDefinedComponents())schema.append(String.format("  +0x%x %s %s // %s\n",c.getOffset(),c.getDataType().getName(),c.getFieldName(),c.getComment()));
        }
        Files.writeString(dest.resolve("partial-structures.txt"),schema.toString());
        super.run();
    }
}
