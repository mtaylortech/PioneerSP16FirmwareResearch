/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

/* WARNING: Unknown calling convention -- yet parameter storage is locked */
/* SUPPORTED ANALYST INTERPRETATION; address identity retained. r0 is constructor destination;
   original UIThread/UIThreadTimer strings and RTTI. Original source signature is not recovered. */

void * UIThread_construct_0056cd14(void *thread)

{
  uint *puVar1;
  undefined4 uVar2;
  void *pvVar3;
  undefined8 *puVar4;
  uint uVar5;
  void *pvVar6;
  uint uVar7;
  uint uVar8;
  int iVar9;
  uint uVar10;
  int iVar11;
  undefined1 auStack_28 [4];
  undefined1 auStack_24 [8];
  
  FUN_0064a3fc(auStack_28,DAT_0056cfcc);
  FUN_00637dc8(thread,auStack_28);
  FUN_00627f38(auStack_28);
  iVar11 = DAT_0056cfd0;
  *(int *)((int)thread + 0xd4) = DAT_0056cfd0 + 0x18;
  *(int *)thread = iVar11;
  *(undefined2 *)((int)thread + 0x2f0) = 0;
  FUN_00644ca8((int)thread + 0x2f4);
  FUN_00644ca8((int)thread + 0x30c);
  *(undefined4 *)((int)thread + 0x324) = 0;
  *(undefined4 *)((int)thread + 0x328) = 0;
  FUN_0064a3fc(auStack_24,DAT_0056cfd4);
  FUN_00637dc8((int)thread + 0x330,auStack_24);
  FUN_00627f38(auStack_24);
  puVar1 = DAT_0056cfd8;
  *(undefined4 *)((int)thread + 0x408) = 0;
  *(undefined4 *)((int)thread + 0x40c) = 0;
  uVar2 = DAT_0056cfdc;
  uVar10 = *puVar1;
  *(undefined4 *)((int)thread + 0x410) = 0;
  *(uint *)((int)thread + 0xdc) = uVar10;
  *(undefined4 *)((int)thread + 0x330) = uVar2;
  *(uint *)((int)thread + 0xe4) = uVar10;
  *(undefined4 *)((int)thread + 0x404) = 10;
  pvVar3 = operator_new__(uVar10);
  iVar11 = uVar10 - 1;
  if (uVar10 != 0) {
    uVar5 = -(int)pvVar3 & 7U;
    if (uVar10 < (-(int)pvVar3 & 7U)) {
      uVar5 = uVar10;
    }
    pvVar6 = pvVar3;
    if (uVar5 != 0) {
      uVar7 = 0;
      do {
        *(undefined1 *)((int)pvVar3 + uVar7) = 0;
        iVar11 = (uVar10 - 2) - uVar7;
        uVar7 = uVar7 + 1;
        pvVar6 = (void *)((int)pvVar6 + 1);
      } while (uVar7 < uVar5);
      if (uVar10 == uVar5) goto LAB_0056ce80;
    }
    uVar7 = uVar10 - uVar5 >> 3;
    if (uVar7 != 0) {
      puVar4 = (undefined8 *)((int)pvVar3 + uVar5);
      uVar8 = 0;
      do {
        uVar8 = uVar8 + 1;
        *puVar4 = 0;
        puVar4 = puVar4 + 1;
      } while (uVar8 < uVar7);
      pvVar6 = (void *)((int)pvVar6 + uVar7 * 8);
      iVar11 = iVar11 + uVar7 * -8;
      if (uVar10 - uVar5 == uVar7 * 8) goto LAB_0056ce80;
    }
    iVar9 = 0;
    do {
      *(undefined1 *)((int)pvVar6 + iVar9) = 0;
      iVar9 = iVar9 + 1;
    } while (iVar9 != iVar11 + 1);
  }
LAB_0056ce80:
  uVar10 = *(uint *)((int)thread + 0xe4);
  *(void **)((int)thread + 0xd8) = pvVar3;
  pvVar3 = operator_new__(uVar10);
  iVar11 = uVar10 - 1;
  if (uVar10 != 0) {
    uVar5 = -(int)pvVar3 & 7U;
    if (uVar10 < (-(int)pvVar3 & 7U)) {
      uVar5 = uVar10;
    }
    pvVar6 = pvVar3;
    if (uVar5 != 0) {
      uVar7 = 0;
      do {
        *(undefined1 *)((int)pvVar3 + uVar7) = 0;
        iVar11 = (uVar10 - 2) - uVar7;
        uVar7 = uVar7 + 1;
        pvVar6 = (void *)((int)pvVar6 + 1);
      } while (uVar7 < uVar5);
      if (uVar10 == uVar5) goto LAB_0056cf38;
    }
    uVar7 = uVar10 - uVar5 >> 3;
    if (uVar7 != 0) {
      puVar4 = (undefined8 *)((int)pvVar3 + uVar5);
      uVar8 = 0;
      do {
        uVar8 = uVar8 + 1;
        *puVar4 = 0;
        puVar4 = puVar4 + 1;
      } while (uVar8 < uVar7);
      pvVar6 = (void *)((int)pvVar6 + uVar7 * 8);
      iVar11 = iVar11 + uVar7 * -8;
      if (uVar10 - uVar5 == uVar7 * 8) goto LAB_0056cf38;
    }
    iVar9 = 0;
    do {
      *(undefined1 *)((int)pvVar6 + iVar9) = 0;
      iVar9 = iVar9 + 1;
    } while (iVar9 != iVar11 + 1);
  }
LAB_0056cf38:
  *(void **)((int)thread + 0xe0) = pvVar3;
  memset(*(void **)((int)thread + 0xd8),0,*(size_t *)((int)thread + 0xdc));
  memset(*(void **)((int)thread + 0xe0),0,*(size_t *)((int)thread + 0xe4));
  FUN_00508d0c((int)thread + 0xe8,1);
  return thread;
}

