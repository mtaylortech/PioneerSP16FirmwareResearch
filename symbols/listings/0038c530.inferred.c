/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0038c530(undefined4 param_1,int *param_2)

{
  int iVar1;
  void *pvVar2;
  undefined4 uVar3;
  undefined4 uVar4;
  void *pvVar5;
  int iVar6;
  uint uVar7;
  int iVar8;
  int iVar9;
  undefined4 uVar10;
  
  param_2[2] = 0;
  iVar6 = 0;
  iVar1 = FUN_00760ee8(param_1);
  if (0 < iVar1) {
    do {
      iVar1 = FUN_00760ef0(param_1,iVar6);
      if ((iVar1 != 0) && ((*(byte *)(iVar1 + 0x68) & 2) != 0)) {
        iVar8 = param_2[2];
        iVar9 = iVar8 + 1;
        if ((param_2[1] < iVar9) &&
           (uVar7 = iVar9 + iVar9 / 2 + 8U & 0xfffffff8, param_2[1] != uVar7)) {
          pvVar2 = (void *)*param_2;
          if ((int)uVar7 < 1) {
            free(pvVar2);
            iVar8 = param_2[2];
            pvVar2 = (void *)0x0;
            *param_2 = 0;
            iVar9 = iVar8 + 1;
            param_2[1] = uVar7;
          }
          else {
            if (pvVar2 == (void *)0x0) {
              pvVar2 = malloc(uVar7 << 4);
              *param_2 = (int)pvVar2;
            }
            else {
              pvVar2 = realloc(pvVar2,uVar7 << 4);
              iVar8 = param_2[2];
              iVar9 = iVar8 + 1;
              *param_2 = (int)pvVar2;
            }
            param_2[1] = uVar7;
          }
        }
        else {
          pvVar2 = (void *)*param_2;
        }
        pvVar5 = (void *)((int)pvVar2 + iVar8 * 0x10);
        param_2[2] = iVar9;
        if (pvVar5 != (void *)0x0) {
          uVar10 = *(undefined4 *)(iVar1 + 0x14);
          uVar3 = *(undefined4 *)(iVar1 + 0x18);
          uVar4 = *(undefined4 *)(iVar1 + 0x1c);
          *(undefined4 *)((int)pvVar2 + iVar8 * 0x10) = *(undefined4 *)(iVar1 + 0x10);
          *(undefined4 *)((int)pvVar5 + 4) = uVar10;
          *(undefined4 *)((int)pvVar5 + 8) = uVar3;
          *(undefined4 *)((int)pvVar5 + 0xc) = uVar4;
        }
      }
      iVar6 = iVar6 + 1;
      iVar1 = FUN_00760ee8(param_1);
    } while (iVar6 < iVar1);
  }
  return;
}

