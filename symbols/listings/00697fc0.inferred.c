/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

/* SUPPORTED ANALYST INTERPRETATION; address identity retained. X11 imports, DISPLAY, socketpair,
   auxiliary window. Original source signature is not recovered. */

void juce_x11_queue_bootstrap_00697fc0(void)

{
  byte bVar1;
  int iVar2;
  undefined4 uVar3;
  char *pcVar4;
  uint uVar5;
  int iVar6;
  void *pvVar7;
  uint uVar8;
  uint uVar9;
  uint uVar10;
  int iVar11;
  _union_1051 local_168;
  undefined1 auStack_164 [128];
  undefined4 local_e4;
  sigset_t sStack_dc;
  undefined1 auStack_5c [40];
  undefined4 local_34;
  undefined1 auStack_20 [4];
  byte *local_1c;
  undefined1 auStack_18 [4];
  undefined4 local_14;
  
  iVar2 = DAT_00698250;
  if (*(int *)(DAT_00698250 + 0x3c) != 0) {
    if (*(char *)(DAT_00698250 + 0x4c) == '\0') {
      iVar6 = XInitThreads();
      if (iVar6 == 0) {
        FUN_0064a3fc(auStack_20,DAT_00698268);
        FUN_00647ca0(auStack_20);
        FUN_00627f38(auStack_20);
        FUN_0064582c();
        return;
      }
      *(undefined1 *)(iVar2 + 0x4c) = 1;
    }
    uVar3 = XSetIOErrorHandler(DAT_00698254);
    *(undefined4 *)(iVar2 + 0x44) = uVar3;
    uVar3 = XSetErrorHandler(DAT_00698258);
    *(undefined4 *)(iVar2 + 0x48) = uVar3;
    sigemptyset(&sStack_dc);
    local_168 = DAT_0069825c;
    memcpy(auStack_164,&sStack_dc,0x80);
    local_e4 = 0;
    sigaction(2,(sigaction *)&local_168,(sigaction *)0x0);
  }
  if (*(int *)(iVar2 + 0x50) == 0) {
    pvVar7 = operator_new(0x34);
    FUN_00644ca8();
    *(undefined4 *)((int)pvVar7 + 0x18) = 0;
    *(undefined4 *)((int)pvVar7 + 0x1c) = 0;
    *(undefined4 *)((int)pvVar7 + 0x20) = 0;
    *(undefined4 *)((int)pvVar7 + 0x2c) = 0;
    *(undefined4 *)((int)pvVar7 + 0x30) = 0;
    socketpair(1,1,0,(int *)((int)pvVar7 + 0x24));
    *(void **)(DAT_00698250 + 0x50) = pvVar7;
  }
  pcVar4 = getenv(DAT_00698260);
  FUN_0064a3fc(&local_1c,pcVar4);
  bVar1 = *local_1c;
  uVar5 = (uint)bVar1;
  if ((bVar1 & 0x80) != 0) {
    if ((bVar1 & 0x40) == 0) {
      uVar5 = uVar5 & 0x7f;
    }
    else {
      uVar10 = 0x40;
      uVar9 = 0;
      uVar8 = 0x7f;
      do {
        uVar10 = uVar10 >> 1;
        uVar8 = uVar8 >> 1;
        uVar9 = uVar9 + 1;
      } while (0x10 < uVar10 && (uVar10 & uVar5) != 0);
      uVar5 = uVar8 & uVar5;
      if ((uVar9 != 0) && (uVar10 = (uint)local_1c[1], (uVar10 & 0xc0) == 0x80)) {
        uVar8 = 1;
        do {
          uVar8 = uVar8 + 1;
          uVar5 = uVar10 & 0x3f | uVar5 << 6;
          if (uVar9 < uVar8) break;
          uVar10 = (uint)local_1c[uVar8];
        } while ((uVar10 & 0xc0) == 0x80);
      }
    }
  }
  if (uVar5 == 0) {
    FUN_0064a3fc(auStack_18,DAT_00698264);
    FUN_0062ad54(&local_1c,auStack_18);
    FUN_00627f38(auStack_18);
  }
  FUN_00636200(&local_14,&local_1c);
  iVar6 = XOpenDisplay(local_14);
  *(int *)(iVar2 + 0x40) = iVar6;
  if (iVar6 != 0) {
    uVar3 = XrmUniqueQuark();
    iVar6 = *(int *)(iVar2 + 0x40);
    *(undefined4 *)(iVar2 + 0x54) = uVar3;
    local_34 = 0;
    iVar11 = *(int *)(iVar6 + 0x8c) + *(int *)(iVar6 + 0x84) * 0x50;
    uVar3 = XCreateWindow(iVar6,*(undefined4 *)(iVar11 + 8),0,0,1,1,0,0,2,
                          *(undefined4 *)(iVar11 + 0x28),0x800,auStack_5c);
    *(undefined4 *)(iVar2 + 0x58) = uVar3;
  }
  FUN_00627f38(&local_1c);
  return;
}

