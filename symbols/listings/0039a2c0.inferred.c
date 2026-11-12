/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_0039a2c0(undefined4 param_1,float param_2,float param_3)

{
  undefined4 uVar1;
  float extraout_r0;
  float extraout_r0_00;
  undefined4 extraout_r0_01;
  undefined4 extraout_r0_02;
  undefined4 extraout_r0_03;
  undefined4 extraout_r0_04;
  undefined4 extraout_r0_05;
  undefined4 extraout_r0_06;
  undefined4 extraout_r0_07;
  undefined4 extraout_r0_08;
  undefined4 extraout_r1;
  undefined4 extraout_r1_00;
  undefined4 extraout_r1_01;
  undefined4 extraout_r1_02;
  undefined4 extraout_r1_03;
  undefined4 extraout_r1_04;
  undefined4 extraout_r1_05;
  undefined4 extraout_r1_06;
  uint in_fpscr;
  float fVar2;
  undefined4 extraout_s1;
  undefined4 extraout_s1_00;
  undefined4 extraout_s1_01;
  undefined4 extraout_s1_02;
  undefined4 extraout_s1_03;
  undefined4 extraout_s1_04;
  int iVar3;
  float fVar4;
  undefined1 auStack_5c [32];
  undefined1 auStack_3c [12];
  undefined1 auStack_30 [4];
  undefined1 auStack_2c [8];
  
  FUN_0062ab08(auStack_30);
  uVar1 = FUN_006d3360(param_1);
  fVar2 = (float)FUN_006cf768(auStack_3c,param_1);
  fVar4 = (float)VectorSignedToFloat(uVar1,(byte)(in_fpscr >> 0x16) & 3);
  fVar2 = floorf(fVar2);
  floorf(fVar2);
  FUN_006c1630(auStack_2c,DAT_0039a7c4);
  FUN_0070acf0(auStack_3c,auStack_2c);
  FUN_006a0280(auStack_2c);
  FUN_006cfc94(auStack_3c,0x3f800000);
  uVar1 = FUN_006c7f40(auStack_5c);
  fVar2 = (param_2 + param_2) * param_3 - param_2;
  if (0.0 <= fVar2) {
    if (fVar2 <= 0.0) {
      FUN_006cfe10(auStack_3c,0,0,(int)extraout_r0_00,(int)fVar4);
      goto LAB_0039a388;
    }
    iVar3 = (int)extraout_r0_00;
    uVar1 = FUN_006cfe10(auStack_3c,0,0,iVar3,(int)fVar4);
    if (fVar2 <= DAT_0039a7b8) {
      tan((double)CONCAT44(extraout_s1_00,uVar1));
      FUN_006ca884(auStack_5c,extraout_r0,extraout_r0 + 1.0,extraout_r0,0,
                   extraout_r0 +
                   (float)(double)CONCAT44(extraout_r1_02,extraout_r0_04) * extraout_r0_00,0);
    }
    else if (fVar2 <= DAT_0039a7bc) {
      tan((double)CONCAT44(extraout_s1_00,uVar1));
      FUN_006ca918(auStack_5c,extraout_r0,extraout_r0 + 1.0,extraout_r0,0,fVar4,0,fVar4,
                   (extraout_r0 + 1.0) -
                   (float)(double)CONCAT44(extraout_r1_04,extraout_r0_06) * extraout_r0_00);
    }
    else if (fVar2 <= DAT_0039a7c0) {
      uVar1 = FUN_006cfe10(auStack_3c,(int)extraout_r0,0,iVar3,iVar3);
      tan((double)CONCAT44(extraout_s1_04,uVar1));
      fVar2 = extraout_r0 + 1.0;
      FUN_006ca884(auStack_5c,extraout_r0,fVar2,fVar4,fVar2,fVar4,
                   fVar2 + (float)(double)CONCAT44(extraout_r1_06,extraout_r0_08) * extraout_r0_00);
    }
    else {
      if (param_2 <= fVar2) {
        FUN_006cfe10(auStack_3c,(int)extraout_r0,0,iVar3,(int)fVar4);
        goto LAB_0039a388;
      }
      uVar1 = FUN_006cfe10(auStack_3c,(int)extraout_r0,0,iVar3,iVar3);
      tan((double)CONCAT44(extraout_s1_01,uVar1));
      FUN_006ca918(auStack_5c,extraout_r0,extraout_r0 + 1.0,fVar4,extraout_r0 + 1.0,fVar4,fVar4,
                   extraout_r0 +
                   (float)(double)CONCAT44(extraout_r1,extraout_r0_01) * extraout_r0_00,fVar4);
    }
  }
  else {
    fVar2 = -fVar2;
    if (param_2 <= fVar2) goto LAB_0039a388;
    if (DAT_0039a7c0 <= fVar2) {
      tan((double)CONCAT44(extraout_s1,uVar1));
      fVar2 = extraout_r0 + 1.0;
      FUN_006ca884(auStack_5c,fVar2,extraout_r0,fVar2,fVar4,
                   fVar2 - (float)(double)CONCAT44(extraout_r1_01,extraout_r0_03) * extraout_r0_00,
                   fVar4);
    }
    else if (DAT_0039a7bc <= fVar2) {
      tan((double)CONCAT44(extraout_s1,uVar1));
      FUN_006ca918(auStack_5c,extraout_r0 + 1.0,extraout_r0,extraout_r0 + 1.0,fVar4,0,fVar4,0,
                   extraout_r0 +
                   (float)(double)CONCAT44(extraout_r1_05,extraout_r0_07) * extraout_r0_00);
    }
    else if (fVar2 < DAT_0039a7b8) {
      uVar1 = FUN_006cfe10(auStack_3c,0,(int)extraout_r0,(int)extraout_r0_00,(int)extraout_r0_00);
      tan((double)CONCAT44(extraout_s1_03,uVar1));
      fVar2 = extraout_r0 + 1.0;
      FUN_006ca918(auStack_5c,fVar2,fVar2,0,fVar2,0,0,
                   fVar2 - (float)(double)CONCAT44(extraout_r1_03,extraout_r0_05) * extraout_r0_00,0
                  );
    }
    else {
      uVar1 = FUN_006cfe10(auStack_3c,0,(int)extraout_r0,(int)extraout_r0_00,(int)extraout_r0_00);
      tan((double)CONCAT44(extraout_s1_02,uVar1));
      fVar2 = extraout_r0 + 1.0;
      FUN_006ca884(auStack_5c,fVar2,fVar2,0,fVar2,0,
                   fVar2 - (float)(double)CONCAT44(extraout_r1_00,extraout_r0_02) * extraout_r0_00);
    }
  }
  FUN_006cff80(auStack_3c,auStack_5c,DAT_0039a7c8);
LAB_0039a388:
  FUN_006c7f70(auStack_5c);
  FUN_006cf7b8(auStack_3c);
  FUN_00627f38(auStack_30);
  return;
}

