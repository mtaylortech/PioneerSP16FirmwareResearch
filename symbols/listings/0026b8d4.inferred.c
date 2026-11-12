/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void candidate_0026b8d4(int param_1,int *param_2,int param_3)

{
  uint uVar1;
  int iVar2;
  int iVar3;
  int *piVar4;
  int iVar5;
  undefined1 uStack_19;
  
  piVar4 = *(int **)(param_1 + 0x128);
  if ((piVar4 != (int *)0x0) && (((uint)piVar4 & 3) == 0)) {
    uVar1 = (int)piVar4 + *(int *)(*piVar4 + -0xc);
    if ((uVar1 != 0) &&
       (((uVar1 & 3) == 0 && (*(int *)((int)piVar4 + *(int *)(*piVar4 + -0xc)) == 0x5e715e28)))) {
      iVar2 = (**(code **)(*param_2 + 8))(param_2);
      if (iVar2 != 0) {
        return;
      }
      if (*(char *)(param_1 + 0x6a8) == '\0') {
        iVar2 = FUN_002f32e8(param_1 + 0x20);
        uVar1 = param_3 + iVar2;
        if ((int)uVar1 < 0) {
          uVar1 = uVar1 + 0x10;
        }
        else if (0xf < (int)uVar1) {
          uVar1 = uVar1 - 0x10;
        }
        iVar2 = *(int *)(param_1 + 0x24);
        if (0xf < uVar1) {
          return;
        }
        if (uVar1 == *(uint *)(iVar2 + 0x54)) {
          return;
        }
        *(undefined4 *)(iVar2 + 0x50) = 0;
        *(uint *)(iVar2 + 0x54) = uVar1;
        *(undefined4 *)(iVar2 + (uVar1 + 0x1028) * 4) = 0x18;
        return;
      }
      iVar5 = param_1 + 0x20;
      uStack_19 = 0;
      iVar2 = FUN_002f32e8(iVar5);
      iVar3 = FUN_002f3d94(iVar5,&uStack_19);
      param_1 = param_1 + iVar2 * 0x1c;
      iVar2 = *(int *)(param_1 + 0x16c);
      if (iVar2 <= param_3 + iVar3) {
        iVar3 = FUN_002f3d94(iVar5,&uStack_19);
        iVar2 = *(int *)(param_1 + 0x170);
        if (param_3 + iVar3 <= iVar2) {
          iVar2 = FUN_002f3d94(iVar5,&uStack_19);
          iVar2 = param_3 + iVar2;
        }
      }
      FUN_002f3ff4(iVar5,iVar2);
      return;
    }
  }
  FUN_004f782c(DAT_0026ba2c,DAT_0026ba30,DAT_0026ba34);
  return;
}

