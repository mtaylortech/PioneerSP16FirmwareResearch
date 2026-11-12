// ---------------------------------------------------------------------------
// SP-16 open research — original research Ghidra script, unchanged below.
// Ghidra script: metadata-only rename of a closed program in a project.
// Original path: ghidra/scripts/SP16RenameProgram.java
// Original SHA-256: 1724473ba3f6bd0ac1749e6deb2ac75191704713251697f56aed167643922ac8
// License: MIT (see repository LICENSE). Addresses refer to the firmware
// version named in the script/docs; they are wrong for other versions.
// ---------------------------------------------------------------------------
// Metadata-only operation on a closed program in the working project.
//@category PioneerSP16
import ghidra.app.script.GhidraScript;
import ghidra.framework.model.DomainFile;
public class SP16RenameProgram extends GhidraScript {
    public void run()throws Exception{
        DomainFile f=state.getProject().getProjectData().getRootFolder().getFile("EP085_Main_R");
        if(f==null)throw new IllegalStateException("Expected source program missing");
        f=f.setName("EP085_Main_R_fw160");println("STATIC_RENAME_OK "+f.getPathname());
    }
}
