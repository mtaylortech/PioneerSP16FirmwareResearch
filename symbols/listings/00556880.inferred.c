/* INFERRED PSEUDOCODE; names/types/indirect targets need instruction checks. No target execution. */

undefined1 * FUN_00556880(undefined1 *param_1)

{
  int iVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  undefined1 *puVar5;
  undefined1 auStack_44 [4];
  undefined1 auStack_40 [4];
  undefined1 auStack_3c [4];
  undefined1 auStack_38 [4];
  undefined1 auStack_34 [4];
  undefined1 auStack_30 [4];
  undefined1 auStack_2c [8];
  
  *param_1 = 0;
  *(undefined4 *)(param_1 + 4) = 0;
  *(undefined4 *)(param_1 + 8) = 0;
  *(undefined4 *)(param_1 + 0xc) = 0;
  *(undefined4 *)(param_1 + 0x10) = 0;
  *(undefined4 *)(param_1 + 0x14) = 0;
  *(undefined4 *)(param_1 + 0x18) = 0;
  *(undefined4 *)(param_1 + 0x1c) = 0;
  *(undefined4 *)(param_1 + 0x20) = 0;
  *(undefined4 *)(param_1 + 0x24) = 0;
  param_1[0xa8] = 1;
  FUN_0055b0f8(param_1 + 0xac);
  FUN_0055b0f8(param_1 + 0xd4);
  FUN_0055b0f8(param_1 + 0xfc);
  FUN_0055b0f8(param_1 + 0x124);
  FUN_0055b0f8(param_1 + 0x14c);
  FUN_0055b0f8(param_1 + 0x174);
  FUN_0055b0f8(param_1 + 0x19c);
  FUN_0055b0f8(param_1 + 0x1c4);
  FUN_0055b0f8(param_1 + 0x1ec);
  FUN_0055b0f8(param_1 + 0x214);
  FUN_0055b0f8(param_1 + 0x23c);
  FUN_0055b0f8(param_1 + 0x264);
  FUN_0055b0f8(param_1 + 0x28c);
  FUN_0055b0f8(param_1 + 0x2b4);
  FUN_0055b0f8(param_1 + 0x2dc);
  FUN_0055b0f8(param_1 + 0x304);
  FUN_0055b0f8(param_1 + 0x32c);
  FUN_0055b0f8(param_1 + 0x354);
  FUN_0055b0f8(param_1 + 0x37c);
  FUN_0055b0f8(param_1 + 0x3a4);
  FUN_0055b0f8(param_1 + 0x3cc);
  FUN_0055b0f8(param_1 + 0x3f4);
  FUN_0055b0f8(param_1 + 0x41c);
  FUN_0055b0f8(param_1 + 0x444);
  FUN_0055b0f8(param_1 + 0x46c);
  FUN_0055b0f8(param_1 + 0x494);
  FUN_0055b0f8(param_1 + 0x4bc);
  FUN_0055b0f8(param_1 + 0x4e4);
  FUN_0055b0f8(param_1 + 0x50c);
  FUN_0055b0f8(param_1 + 0x534);
  FUN_0055b0f8(param_1 + 0x55c);
  FUN_0055b0f8(param_1 + 0x584);
  FUN_0055b0f8(param_1 + 0x5ac);
  FUN_0055b0f8(param_1 + 0x5d4);
  FUN_0055b0f8(param_1 + 0x5fc);
  FUN_0055b0f8(param_1 + 0x624);
  FUN_0055b0f8(param_1 + 0x64c);
  FUN_0055ee5c(param_1 + 0x674);
  FUN_0055ee5c(param_1 + 0x69c);
  FUN_0055ee5c(param_1 + 0x6c4);
  FUN_0055b5bc(param_1 + 0x6ec);
  FUN_0055b5bc(param_1 + 0x740);
  FUN_0055b5bc(param_1 + 0x794);
  FUN_0055b5bc(param_1 + 0x7e8);
  FUN_0055b5bc(param_1 + 0x83c);
  FUN_0055b5bc(param_1 + 0x890);
  FUN_0055b5bc(param_1 + 0x8e4);
  FUN_0055b5bc(param_1 + 0x938);
  FUN_0055b5bc(param_1 + 0x98c);
  FUN_0055b5bc(param_1 + 0x9e0);
  FUN_0055b5bc(param_1 + 0xa34);
  FUN_0055b5bc(param_1 + 0xa88);
  FUN_0055b5bc(param_1 + 0xadc);
  FUN_0055b5bc(param_1 + 0xb30);
  FUN_0055b5bc(param_1 + 0xb84);
  FUN_0055b5bc(param_1 + 0xbd8);
  FUN_0055ce44(param_1 + 0xc2c);
  FUN_0055e7d4(param_1 + 0xcd0);
  FUN_0055c0a0(param_1 + 0xcf4);
  FUN_0055c0a0(param_1 + 0xd5c);
  FUN_0055c0a0(param_1 + 0xdc4);
  FUN_0055c0a0(param_1 + 0xe2c);
  FUN_0055c0a0(param_1 + 0xe94);
  FUN_0055c0a0(param_1 + 0xefc);
  FUN_0055c0a0(param_1 + 0xf64);
  FUN_00555ca4(param_1 + 0xfcc);
  FUN_00666e84(auStack_40,DAT_0055727c);
  puVar5 = param_1 + 0xfe0;
  FUN_0068ac80(puVar5,auStack_40);
  FUN_006280c8(auStack_40);
  FUN_00666e84(auStack_44,DAT_00557280);
  FUN_0068ac80(param_1 + 0xff0,auStack_44);
  FUN_006280c8(auStack_44);
  FUN_00644ca8(param_1 + 0x1000);
  FUN_00644ca8(param_1 + 0x1018);
  *(undefined4 *)(param_1 + 0x1030) = 0;
  *(undefined4 *)(param_1 + 0x1034) = 0;
  *(undefined4 *)(param_1 + 0x1038) = 0;
  iVar1 = FUN_00554dd8(puVar5);
  if (iVar1 != 0) {
    iVar4 = 0;
    iVar1 = iVar4;
    do {
      FUN_0064a3fc(auStack_30,DAT_00557284);
      iVar3 = iVar1 + 1;
      FUN_0062d868(auStack_34,iVar3);
      FUN_0062f808(auStack_2c,auStack_30,auStack_34);
      FUN_00663f10(auStack_3c,auStack_2c);
      FUN_00627f38(auStack_2c);
      FUN_00627f38(auStack_34);
      FUN_00627f38(auStack_30);
      FUN_00627ba0(auStack_38,auStack_3c);
      FUN_0068b048(puVar5,auStack_38);
      iVar2 = FUN_0061f7c4();
      FUN_006280c8(auStack_38);
      FUN_006280c8(auStack_3c);
      FUN_0055b708(param_1 + 0x6ec + iVar1 * 0x54,iVar2,0x36a);
      if (0x1c8 < iVar2 - 0x30U) {
        iVar4 = 1;
      }
      iVar1 = iVar3;
    } while (iVar3 != 0x10);
    if (iVar4 == 0) {
      *param_1 = 1;
      goto LAB_00556ce0;
    }
  }
  *param_1 = 2;
LAB_00556ce0:
  memset(param_1 + 0x28,0,0x80);
  return param_1;
}

