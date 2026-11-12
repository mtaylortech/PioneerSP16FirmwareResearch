/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

/* WARNING: Unknown calling convention -- yet parameter storage is locked */
/* SUPPORTED ANALYST INTERPRETATION; address identity retained. r0 saved as this at 0056c4c0 and
   returned at 0056c558; r1 is settings path, r2 is forwarded into base constructor. Surviving
   Settings::Settings() diagnostic. Original source signature is not recovered. */

void * Settings_construct_0056c4bc(void *settings,char *path,char *settings_label)

{
  int iVar1;
  int *piVar2;
  undefined4 uVar3;
  undefined4 *puVar4;
  char *pcVar5;
  
  FUN_006978c8();
  iVar1 = DAT_0056c5b0;
  *(undefined4 *)((int)settings + 0x18) = 0;
  *(int *)((int)settings + 0x14) = iVar1 + 0x1c;
  *(undefined4 *)((int)settings + 0x1c) = 0xffffffff;
  *(int *)settings = iVar1;
  FUN_00567c0c((int)settings + 0x20,0x40,DAT_0056c5b4);
  FUN_00567f44((int)settings + 0x270,0x40);
  piVar2 = DAT_0056c5b8;
  *(undefined1 *)((int)settings + 0x324) = 0;
  *(undefined4 *)((int)settings + 0x328) = 0;
  if (*piVar2 == 0) {
    *piVar2 = (int)settings;
    pcVar5 = DAT_0056c5bc;
    if ((path != (char *)0x0) && (pcVar5 = path, *path == '\0')) {
      pcVar5 = DAT_0056c5bc;
    }
    FUN_0056a7f0(settings,pcVar5);
    return settings;
  }
  puVar4 = (undefined4 *)__cxa_allocate_exception(4);
  uVar3 = DAT_0056c5c4;
  *puVar4 = DAT_0056c5c0;
                    /* WARNING: Subroutine does not return */
  __cxa_throw(puVar4,uVar3,0);
}

