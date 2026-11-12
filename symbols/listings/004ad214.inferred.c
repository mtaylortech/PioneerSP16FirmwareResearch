/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

undefined4 FUN_004ad214(undefined4 param_1,undefined4 param_2,undefined4 *param_3,int param_4)

{
  int iVar1;
  undefined4 uVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  int *piVar6;
  int iVar7;
  int local_30 [3];
  
  iVar5 = DAT_004ad300;
  *param_3 = 0;
  iVar3 = 0;
  iVar4 = 0;
  *(undefined4 *)(param_4 + 8) = 0;
  do {
    piVar6 = *(int **)(iVar5 + iVar3);
    FUN_00627ba0(local_30,param_2);
    iVar1 = local_30[0];
    iVar3 = iVar3 + 0x28;
    iVar7 = *piVar6;
    FUN_006280c8(local_30);
    if (iVar7 == iVar1) {
      iVar5 = DAT_004ad300 + iVar4 * 0x28;
      if (*(int *)(iVar5 + 0xc) != 0) {
        uVar2 = (**(code **)(iVar5 + 0x10))(iVar5 + 4,param_1);
        *param_3 = uVar2;
      }
      if (*(int *)(iVar5 + 0x20) != 0) {
        (**(code **)(iVar5 + 0x24))(iVar5 + 0x18,param_1,param_4);
      }
      return *(undefined4 *)(iVar5 + 0x14);
    }
    iVar4 = iVar4 + 1;
  } while (iVar3 != 0x6b8);
  FUN_004f782c(DAT_004ad304,DAT_004ad308,DAT_004ad30c);
  return 0xffffffff;
}

