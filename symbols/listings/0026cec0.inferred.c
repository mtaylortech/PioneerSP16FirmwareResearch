/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0026cec0(int param_1)

{
  uint uVar1;
  int *piVar2;
  int iVar3;
  undefined1 auStack_3c [4];
  undefined1 auStack_38 [4];
  undefined1 auStack_34 [4];
  undefined1 auStack_30 [4];
  undefined1 auStack_2c [4];
  undefined1 auStack_28 [4];
  undefined1 auStack_24 [4];
  undefined1 auStack_20 [4];
  undefined1 auStack_1c [4];
  undefined1 auStack_18 [4];
  undefined1 auStack_14 [4];
  undefined1 auStack_10 [4];
  undefined1 auStack_c [4];
  
  FUN_00627b90(auStack_3c);
  uVar1 = FUN_002fe010(param_1 + 0x20);
  if (uVar1 < 0x14) {
    switch(*(undefined4 *)(DAT_0026d118 + uVar1 * 4 + 0x238)) {
    default:
      FUN_00627ba0(auStack_c,DAT_0026d120);
      FUN_0062abf4(auStack_3c,auStack_c);
      FUN_006280c8(auStack_c);
      break;
    case 1:
      FUN_00627ba0(auStack_34,DAT_0026d124);
      FUN_0062abf4(auStack_3c,auStack_34);
      FUN_006280c8(auStack_34);
      break;
    case 2:
      FUN_00627ba0(auStack_30,DAT_0026d128);
      FUN_0062abf4(auStack_3c,auStack_30);
      FUN_006280c8(auStack_30);
      break;
    case 3:
      FUN_00627ba0(auStack_2c,DAT_0026d12c);
      FUN_0062abf4(auStack_3c,auStack_2c);
      FUN_006280c8(auStack_2c);
      break;
    case 4:
      FUN_00627ba0(auStack_28,DAT_0026d130);
      FUN_0062abf4(auStack_3c,auStack_28);
      FUN_006280c8(auStack_28);
      break;
    case 5:
      FUN_00627ba0(auStack_24,DAT_0026d134);
      FUN_0062abf4(auStack_3c,auStack_24);
      FUN_006280c8(auStack_24);
      break;
    case 6:
      FUN_00627ba0(auStack_20,DAT_0026d138);
      FUN_0062abf4(auStack_3c,auStack_20);
      FUN_006280c8(auStack_20);
      break;
    case 7:
      FUN_00627ba0(auStack_1c,DAT_0026d13c);
      FUN_0062abf4(auStack_3c,auStack_1c);
      FUN_006280c8(auStack_1c);
      break;
    case 8:
      FUN_00627ba0(auStack_18,DAT_0026d140);
      FUN_0062abf4(auStack_3c,auStack_18);
      FUN_006280c8(auStack_18);
      break;
    case 9:
      FUN_00627ba0(auStack_14,DAT_0026d144);
      FUN_0062abf4(auStack_3c,auStack_14);
      FUN_006280c8(auStack_14);
      break;
    case 10:
      FUN_00627ba0(auStack_10,DAT_0026d11c);
      FUN_0062abf4(auStack_3c,auStack_10);
      FUN_006280c8(auStack_10);
      break;
    case 0xffffffff:
      goto switchD_0026cef8_caseD_ffffffff;
    }
  }
  else {
switchD_0026cef8_caseD_ffffffff:
    FUN_00627ba0(auStack_38,DAT_0026d120);
    FUN_0062abf4(auStack_3c,auStack_38);
    FUN_006280c8(auStack_38);
  }
  piVar2 = *(int **)(param_1 + 0x10);
  iVar3 = *piVar2;
  *(undefined4 *)(*(int *)(param_1 + 0x24) + 0x74) = 0;
  (**(code **)(iVar3 + 8))(piVar2,auStack_3c);
  FUN_006280c8(auStack_3c);
  return;
}

