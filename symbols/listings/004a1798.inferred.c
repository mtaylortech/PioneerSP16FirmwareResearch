/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_004a1798(int param_1,int param_2)

{
  undefined4 uVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  uint in_fpscr;
  float fVar6;
  float fVar7;
  undefined1 auStack_44 [4];
  undefined1 auStack_40 [4];
  undefined1 auStack_3c [4];
  undefined1 auStack_38 [4];
  undefined1 auStack_34 [4];
  undefined1 auStack_30 [4];
  undefined1 auStack_2c [2];
  char local_2a;
  undefined1 auStack_28 [4];
  undefined1 auStack_24 [8];
  
  FUN_0062ab08(auStack_44);
  FUN_00636880(auStack_40,DAT_004a19d8);
  FUN_00659dc8(auStack_3c,param_1 + 0xac,auStack_40);
  FUN_00620248(auStack_44,auStack_3c);
  FUN_00627f38(auStack_3c);
  FUN_0070974c(auStack_38,auStack_44);
  FUN_006d3480(auStack_34,auStack_38);
  uVar1 = FUN_006d3360(auStack_34);
  fVar6 = (float)VectorSignedToFloat(uVar1,(byte)(in_fpscr >> 0x16) & 3);
  FUN_006d3188(auStack_30,2,(int)fVar6,(int)fVar6,1);
  if (param_2 == 0) {
    fVar6 = (float)VectorSignedToFloat(*(undefined4 *)(param_1 + 0x11c),(byte)(in_fpscr >> 0x16) & 3
                                      );
    fVar7 = (float)VectorSignedToFloat(*(undefined4 *)(param_1 + 0x118),(byte)(in_fpscr >> 0x16) & 3
                                      );
    FUN_0039a2c0(auStack_30,0x430f0000,fVar6 / fVar7);
  }
  else {
    fVar6 = (float)VectorSignedToFloat(*(undefined4 *)(param_1 + 0x100),(byte)(in_fpscr >> 0x16) & 3
                                      );
    fVar7 = (float)VectorSignedToFloat(*(undefined4 *)(param_1 + 0xfc),(byte)(in_fpscr >> 0x16) & 3)
    ;
    FUN_0039a890(auStack_30,0x430f0000,fVar6 / fVar7);
  }
  FUN_006c1618(auStack_2c);
  iVar2 = FUN_006d3360(auStack_34);
  iVar3 = FUN_006d3370(auStack_34);
  if (0 < iVar2) {
    iVar5 = 0;
    do {
      if (0 < iVar3) {
        iVar4 = 0;
        do {
          while( true ) {
            FUN_006d38e8(auStack_28,auStack_30,iVar5,iVar4);
            FUN_006c1648(auStack_2c,auStack_28);
            FUN_006a0280(auStack_28);
            if (local_2a != '\0') break;
            FUN_006c207c(auStack_24,auStack_2c);
            FUN_006d39b0(auStack_34,iVar5,iVar4,auStack_24);
            iVar4 = iVar4 + 1;
            FUN_006a0280(auStack_24);
            if (iVar4 == iVar3) goto LAB_004a1908;
          }
          iVar4 = iVar4 + 1;
        } while (iVar4 != iVar3);
      }
LAB_004a1908:
      iVar5 = iVar5 + 1;
    } while (iVar5 != iVar2);
  }
  if (param_2 == 0) {
    FUN_0038e768(*(undefined4 *)(param_1 + 0xb4),auStack_34,DAT_004a19dc);
  }
  else {
    FUN_0038e768(*(undefined4 *)(param_1 + 0xbc),auStack_34,DAT_004a19dc);
  }
  FUN_006a0280(auStack_2c);
  FUN_00707778(auStack_30);
  FUN_00707778(auStack_34);
  FUN_00707778(auStack_38);
  FUN_00627f38(auStack_44);
  return;
}

