// Import the SP-16 analyst labels into a Ghidra program.
//
// Applies symbols/labels-1.60.json to YOUR OWN copy of EP085_Main_R from
// firmware 1.60 (SHA-256 below). Works in the Ghidra GUI (Script Manager: it
// asks for the JSON file) and headless (pass the JSON path as the script
// argument). Plain Java GhidraScript: no Python setup needed.
//
// Safety: refuses to touch any program whose SHA-256 is not the 1.60 binary.
// Addresses from one firmware version are WRONG for every other version.
//
// The names are inferred analyst names, not original source names. Every
// label with a rationale also gets it as a plate comment prefixed
// "[SP16 inferred]". Imports (kind "import") are skipped: Ghidra's ELF
// loader already names them.
//
// Tested 2026-11-11 with Ghidra 12.1.4, headless, after full auto-analysis.
// License: MIT (see repository LICENSE).
//@category SP16

import java.io.File;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;

public class SP16ImportLabels extends GhidraScript {

    static final String EXPECTED_SHA256 =
        "3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464";

    @Override
    protected void run() throws Exception {
        String actual = currentProgram.getExecutableSHA256();
        if (actual == null || !actual.equalsIgnoreCase(EXPECTED_SHA256)) {
            printerr("SP16 refusing to import: program SHA-256 is " + actual +
                ", expected " + EXPECTED_SHA256 + " (firmware 1.60 EP085_Main_R).");
            return;
        }
        String[] args = getScriptArgs();
        File file = args.length > 0 ? new File(args[0])
                                    : askFile("Select labels-1.60.json", "Import");
        JsonObject root;
        try (Reader r = Files.newBufferedReader(file.toPath(), StandardCharsets.UTF_8)) {
            root = JsonParser.parseReader(r).getAsJsonObject();
        }

        int functions = 0, labels = 0, comments = 0, imports = 0, failed = 0;
        for (JsonElement element : root.getAsJsonArray("labels")) {
            JsonObject rec = element.getAsJsonObject();
            if ("import".equals(text(rec, "kind"))) {
                imports++;
                continue;
            }
            String name = text(rec, "name");
            Address addr = toAddr(Long.decode(text(rec, "address")));
            try {
                Function func = getFunctionAt(addr);
                if (func != null) {
                    func.setName(name, SourceType.USER_DEFINED);
                    functions++;
                }
                else {
                    createLabel(addr, name, true, SourceType.USER_DEFINED);
                    labels++;
                }
                String why = text(rec, "rationale");
                if (why != null && !why.isEmpty()) {
                    setPlateComment(addr, "[SP16 inferred] " + why);
                    comments++;
                }
            }
            catch (Exception e) {
                printerr("SP16 skip " + addr + " " + name + ": " + e.getMessage());
                failed++;
            }
        }
        println(String.format("SP16 labels applied: %d function names, %d labels, " +
            "%d plate comments; %d imports skipped; %d failed",
            functions, labels, comments, imports, failed));
    }

    private static String text(JsonObject o, String key) {
        JsonElement v = o.get(key);
        return (v == null || v.isJsonNull()) ? null : v.getAsString();
    }
}
