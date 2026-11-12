/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0044c6c4(int param_1,int param_2,undefined4 param_3,int param_4,undefined4 param_5,
                 undefined4 param_6,undefined4 param_7,undefined4 param_8,undefined1 *param_9,
                 undefined4 param_10,undefined4 param_11,undefined4 param_12,undefined4 param_13,
                 undefined4 param_14,undefined1 *param_15,int param_16)

{
  undefined1 uVar1;
  undefined1 uVar2;
  float fVar3;
  int *piVar4;
  undefined4 uVar5;
  int iVar6;
  int iVar7;
  undefined4 uVar8;
  bool bVar9;
  uint in_fpscr;
  float fVar10;
  float fVar11;
  
  fVar3 = DAT_0044cacc;
  bVar9 = param_2 != 0;
  FUN_0044b994(param_1,bVar9);
  FUN_0044ba78(param_1,param_2);
  FUN_0044bb6c(param_1,param_3);
  FUN_0044bf00(param_1,param_14);
  (**(code **)(**(int **)(param_1 + 0x1d4) + 0x2c))(*(int **)(param_1 + 0x1d4),0);
  (**(code **)(**(int **)(param_1 + 0x1d8) + 0x2c))(*(int **)(param_1 + 0x1d8),0);
  (**(code **)(**(int **)(param_1 + 0x1dc) + 0x2c))(*(int **)(param_1 + 0x1dc),0);
  (**(code **)(**(int **)(param_1 + 0x1e0) + 0x2c))(*(int **)(param_1 + 0x1e0),0);
  (**(code **)(**(int **)(param_1 + 0x1e4) + 0x2c))(*(int **)(param_1 + 0x1e4),0);
  (**(code **)(**(int **)(param_1 + 0x1e8) + 0x2c))(*(int **)(param_1 + 0x1e8),0);
  (**(code **)(**(int **)(param_1 + 0x1ec) + 0x2c))(*(int **)(param_1 + 0x1ec),0);
  (**(code **)(**(int **)(param_1 + 0x1f0) + 0x2c))(*(int **)(param_1 + 0x1f0),0);
  (**(code **)(**(int **)(param_1 + 500) + 0x2c))(*(int **)(param_1 + 500),0);
  (**(code **)(**(int **)(param_1 + 0x1f8) + 0x2c))(*(int **)(param_1 + 0x1f8),0);
  (**(code **)(**(int **)(param_1 + 0x1fc) + 0x2c))(*(int **)(param_1 + 0x1fc),0);
  (**(code **)(**(int **)(param_1 + 0x200) + 0x2c))(*(int **)(param_1 + 0x200),0);
  (**(code **)(**(int **)(param_1 + 0x204) + 0x2c))(*(int **)(param_1 + 0x204),0);
  (**(code **)(**(int **)(param_1 + 0x208) + 0x2c))(*(int **)(param_1 + 0x208),0);
  (**(code **)(**(int **)(param_1 + 0x20c) + 0x2c))(*(int **)(param_1 + 0x20c),0);
  (**(code **)(**(int **)(param_1 + 0x210) + 0x2c))(*(int **)(param_1 + 0x210),0);
  *(int *)(param_1 + 0x21c) = param_4;
  piVar4 = *(int **)(param_1 + param_4 * 4 + 0x1d4);
  (**(code **)(*piVar4 + 0x2c))(piVar4,1);
  FUN_0039dafc(*(undefined4 *)(param_1 + 0x184),param_5,param_6);
  FUN_0039dafc(*(undefined4 *)(param_1 + 0x188),param_7,param_8);
  FUN_0039dafc(*(undefined4 *)(param_1 + 0x18c),param_10,param_11);
  FUN_0039dafc(*(undefined4 *)(param_1 + 400),param_12,param_13);
  uVar8 = *(undefined4 *)(param_9 + 8);
  uVar1 = *param_9;
  uVar5 = *(undefined4 *)(param_9 + 0xc);
  uVar2 = param_9[0x10];
  *(undefined4 *)(param_1 + 0x224) = *(undefined4 *)(param_9 + 4);
  *(undefined4 *)(param_1 + 0x228) = uVar8;
  *(undefined1 *)(param_1 + 0x220) = uVar1;
  *(undefined4 *)(param_1 + 0x22c) = uVar5;
  *(undefined1 *)(param_1 + 0x230) = uVar2;
  FUN_0062ab80(param_1 + 0x234,param_9 + 0x14);
  iVar6 = *(int *)(param_9 + 8);
  iVar7 = *(int *)(param_9 + 4);
  fVar10 = (float)VectorSignedToFloat(*(undefined4 *)(param_9 + 0xc),(byte)(in_fpscr >> 0x16) & 3);
  *(undefined4 *)(param_1 + 0x238) = *(undefined4 *)(param_9 + 0x18);
  fVar11 = (float)VectorSignedToFloat(iVar6 - iVar7,(byte)(in_fpscr >> 0x16) & 3);
  FUN_0079c798(*(undefined4 *)(param_1 + 0x17c),*(undefined4 *)(param_1 + 0x214),
               0x177 - (int)((fVar10 / fVar11) * fVar3));
  uVar8 = *(undefined4 *)(param_15 + 8);
  uVar5 = *(undefined4 *)(param_15 + 0xc);
  uVar1 = param_15[0x10];
  uVar2 = *param_15;
  *(undefined4 *)(param_1 + 0x240) = *(undefined4 *)(param_15 + 4);
  *(undefined4 *)(param_1 + 0x244) = uVar8;
  *(undefined4 *)(param_1 + 0x248) = uVar5;
  *(undefined1 *)(param_1 + 0x24c) = uVar1;
  *(undefined1 *)(param_1 + 0x23c) = uVar2;
  FUN_0062ab80(param_1 + 0x250,param_15 + 0x14);
  iVar6 = *(int *)(param_15 + 8);
  iVar7 = *(int *)(param_15 + 4);
  fVar10 = (float)VectorSignedToFloat(*(undefined4 *)(param_15 + 0xc),(byte)(in_fpscr >> 0x16) & 3);
  *(undefined4 *)(param_1 + 0x254) = *(undefined4 *)(param_15 + 0x18);
  fVar11 = (float)VectorSignedToFloat(iVar6 - iVar7,(byte)(in_fpscr >> 0x16) & 3);
  FUN_0079c798(*(undefined4 *)(param_1 + 0x180),*(undefined4 *)(param_1 + 0x218),
               0x177 - (int)((fVar10 / fVar11) * fVar3));
  FUN_004a1ee4(*(undefined4 *)(param_1 + 0x194),param_16,bVar9);
  FUN_004a1ee4(*(undefined4 *)(param_1 + 0x198),param_16 + 0x28,bVar9);
  FUN_004a1ee4(*(undefined4 *)(param_1 + 0x19c),param_16 + 0x50,bVar9);
  FUN_004a1ee4(*(undefined4 *)(param_1 + 0x1a0),param_16 + 0x78,bVar9);
  FUN_004a1ee4(*(undefined4 *)(param_1 + 0x1a4),param_16 + 0xa0,bVar9);
  FUN_004a1ee4(*(undefined4 *)(param_1 + 0x1a8),param_16 + 200,bVar9);
  FUN_004a1ee4(*(undefined4 *)(param_1 + 0x1ac),param_16 + 0xf0,bVar9);
  FUN_004a1ee4(*(undefined4 *)(param_1 + 0x1b0),param_16 + 0x118,bVar9);
  FUN_004a1ee4(*(undefined4 *)(param_1 + 0x1b4),param_16 + 0x140,bVar9);
  FUN_004a1ee4(*(undefined4 *)(param_1 + 0x1b8),param_16 + 0x168,bVar9);
  FUN_004a1ee4(*(undefined4 *)(param_1 + 0x1bc),param_16 + 400,bVar9);
  FUN_004a1ee4(*(undefined4 *)(param_1 + 0x1c0),param_16 + 0x1b8,bVar9);
  FUN_004a1ee4(*(undefined4 *)(param_1 + 0x1c4),param_16 + 0x1e0,bVar9);
  FUN_004a1ee4(*(undefined4 *)(param_1 + 0x1c8),param_16 + 0x208,bVar9);
  FUN_004a1ee4(*(undefined4 *)(param_1 + 0x1cc),param_16 + 0x230,bVar9);
  FUN_004a1ee4(*(undefined4 *)(param_1 + 0x1d0),param_16 + 600,bVar9);
  return;
}

