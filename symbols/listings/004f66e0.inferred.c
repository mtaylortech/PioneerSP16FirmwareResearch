/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_004f66e0(int param_1)

{
  char cVar1;
  undefined4 uVar2;
  int iVar3;
  int iVar4;
  uint uVar5;
  int *piVar6;
  int iVar7;
  uint uVar8;
  int iVar9;
  uint uVar10;
  int iVar11;
  undefined8 local_38;
  undefined1 auStack_30 [8];
  undefined4 local_28;
  undefined4 local_24;
  
  iVar9 = *(int *)(param_1 + 0x38);
  iVar11 = *(int *)(param_1 + 0x3c);
  uVar2 = FUN_0078ca5c();
  iVar3 = FUN_0076360c();
  if (0 < iVar3) {
    piVar6 = (int *)0x0;
    iVar7 = 0;
    do {
      iVar4 = FUN_00763614(uVar2,iVar7);
      iVar7 = iVar7 + 1;
      if ((((*(int *)(iVar4 + 0x10) <= iVar9) && (*(int *)(iVar4 + 0x14) <= iVar11)) &&
          (iVar9 < *(int *)(iVar4 + 0x10) + *(int *)(iVar4 + 0x18))) &&
         (iVar11 < *(int *)(iVar4 + 0x14) + *(int *)(iVar4 + 0x1c))) {
        piVar6 = (int *)FUN_0078ddc8();
      }
    } while (iVar7 != iVar3);
    if (piVar6 != (int *)0x0) {
      local_38 = *(undefined8 *)(param_1 + 0x38);
      FUN_00780b88(auStack_30,piVar6,&local_38);
      if ((*(int *)(param_1 + 0x38) != *(int *)(param_1 + 0x40)) ||
         (*(int *)(param_1 + 0x3c) != *(int *)(param_1 + 0x44))) {
        (**(code **)(*piVar6 + 0x74))
                  (piVar6,param_1 + 0x38,auStack_30,*(undefined1 *)(param_1 + 0x28));
      }
      uVar10 = *(uint *)(param_1 + 0x34);
      if (0 < (int)uVar10) {
        uVar8 = 0;
        uVar5 = uVar10;
        do {
          if (uVar8 < uVar5) {
            cVar1 = *(char *)(*(int *)(param_1 + 0x2c) + uVar8);
            *(char *)(param_1 + 0x28) = cVar1;
            if (cVar1 == '\0') goto LAB_004f6824;
            (**(code **)(*piVar6 + 0x6c))(piVar6,param_1 + 0x38,auStack_30);
          }
          else {
            *(undefined1 *)(param_1 + 0x28) = 0;
LAB_004f6824:
            (**(code **)(*piVar6 + 0x70))(piVar6,param_1 + 0x38,auStack_30);
          }
          if (uVar8 + 1 == uVar10) break;
          uVar8 = uVar8 + 1;
          uVar5 = *(uint *)(param_1 + 0x34);
        } while( true );
      }
      if (*(int *)(param_1 + 0x30) != 0) {
        free(*(void **)(param_1 + 0x2c));
        *(undefined4 *)(param_1 + 0x2c) = 0;
        *(undefined4 *)(param_1 + 0x30) = 0;
      }
      *(undefined4 *)(param_1 + 0x34) = 0;
      FUN_0078ca5c();
      FUN_007a5b40(&local_28);
      *(undefined4 *)(param_1 + 0x38) = local_28;
      *(undefined4 *)(param_1 + 0x3c) = local_24;
      *(undefined4 *)(param_1 + 0x40) = local_28;
      *(undefined4 *)(param_1 + 0x44) = local_24;
    }
  }
  return;
}

