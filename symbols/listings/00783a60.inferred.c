/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

undefined4 FUN_00783a60(int param_1,undefined4 param_2)

{
  int iVar1;
  int iVar2;
  void *__ptr;
  undefined4 uVar3;
  undefined4 uVar4;
  undefined4 uVar5;
  int iVar6;
  int iVar7;
  int iVar8;
  int iVar9;
  undefined1 auStack_30 [4];
  undefined1 auStack_2c [8];
  
  FUN_00697ecc(auStack_2c);
  iVar1 = FUN_006d3360(param_2);
  iVar2 = FUN_006d3370(param_2);
  __ptr = malloc(iVar2 * iVar1 * 4);
  if (0 < iVar2) {
    iVar8 = 0;
    iVar9 = iVar8;
    do {
      if (0 < iVar1) {
        iVar7 = iVar8 << 2;
        iVar6 = 0;
        do {
          FUN_006d38e8(auStack_30,param_2,iVar6,iVar9);
          iVar6 = iVar6 + 1;
          uVar3 = FUN_006c2038(auStack_30);
          iVar8 = iVar8 + 1;
          *(undefined4 *)((int)__ptr + iVar7) = uVar3;
          FUN_006a0280(auStack_30);
          iVar7 = iVar7 + 4;
        } while (iVar6 != iVar1);
      }
      iVar9 = iVar9 + 1;
    } while (iVar9 != iVar2);
  }
  uVar3 = XCreateImage(param_1,0,0x18,2,0,__ptr,iVar1,iVar2,0x20,0);
  uVar4 = XCreatePixmap(param_1,*(undefined4 *)
                                 (*(int *)(param_1 + 0x8c) + *(int *)(param_1 + 0x84) * 0x50 + 8),
                        iVar1,iVar2,0x18);
  uVar5 = XCreateGC(param_1,uVar4,0,0);
  XPutImage(param_1,uVar4,uVar5,uVar3,0,0,0,0,iVar1,iVar2);
  XFreeGC(param_1,uVar5);
  free(__ptr);
  FUN_00697eec(auStack_2c);
  return uVar4;
}

