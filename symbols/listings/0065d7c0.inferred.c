/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

int FUN_0065d7c0(int *param_1,undefined4 *param_2,undefined4 *param_3,undefined4 *param_4)

{
  char *pcVar1;
  int iVar2;
  int iVar3;
  undefined4 *puVar4;
  char *pcVar5;
  int iVar6;
  char *pcVar7;
  int iVar8;
  char *pcVar9;
  bool bVar10;
  char *local_60 [2];
  char *local_58 [2];
  char *local_50 [2];
  int local_48 [2];
  char *local_40 [2];
  char *local_38 [2];
  char *local_30 [3];
  
  pcVar7 = (char *)*param_2;
  iVar8 = 0;
  do {
    pcVar5 = (char *)*param_3;
    pcVar9 = (char *)*param_4;
    iVar3 = 0;
    local_40[0] = pcVar7;
LAB_0065d7fc:
    iVar6 = iVar3;
    pcVar1 = local_40[0];
    if (*local_40[0] != '\0') {
      iVar2 = FUN_0066c200(local_40);
      pcVar1 = pcVar5;
      if (iVar6 == 0) {
        while (local_38[0] = pcVar1, *local_38[0] != '\0') {
          iVar3 = FUN_0066c200(local_38);
          pcVar1 = local_38[0];
          if (iVar2 == iVar3) {
            pcVar1 = local_40[0] + -1;
            if ((((local_40[0][-1] & 0xc0U) == 0x80) &&
                (pcVar1 = local_40[0] + -2, (local_40[0][-2] & 0xc0U) == 0x80)) &&
               (pcVar1 = local_40[0] + -3, (local_40[0][-3] & 0xc0U) == 0x80)) {
              pcVar1 = local_40[0] + -4;
            }
            goto LAB_0065d8c0;
          }
        }
      }
      local_30[0] = pcVar9;
      do {
        iVar3 = iVar6;
        if (*local_30[0] == '\0') goto LAB_0065d7fc;
        iVar3 = FUN_0066c200(local_30);
      } while (iVar2 != iVar3);
      iVar3 = iVar2;
      if ((iVar6 != 0) && (iVar3 = iVar6, iVar2 == iVar6)) {
        iVar3 = 0;
      }
      goto LAB_0065d7fc;
    }
LAB_0065d8c0:
    local_40[0] = pcVar1;
    local_60[0] = local_40[0];
    local_58[0] = local_40[0];
    local_50[0] = pcVar7;
    FUN_0062c75c(local_48,local_50,local_58);
    iVar3 = param_1[2];
    iVar6 = iVar3 + 1;
    if (param_1[1] < iVar6) {
      FUN_00431874(param_1,iVar6 + iVar6 / 2 + 8U & 0xfffffff8);
      iVar3 = param_1[2];
      iVar6 = iVar3 + 1;
    }
    iVar8 = iVar8 + 1;
    param_1[2] = iVar6;
    iVar6 = DAT_0065d9a4;
    bVar10 = *param_1 + iVar3 * 4 != 0;
    if (bVar10) {
      *(int *)(*param_1 + iVar3 * 4) = local_48[0];
      iVar3 = iVar6;
    }
    else {
      iVar6 = local_48[0];
      iVar3 = 0;
    }
    if (bVar10) {
      local_48[0] = iVar3;
    }
    FUN_0066d6f8(iVar6 + -8);
    if (*local_60[0] == '\0') {
      return iVar8;
    }
    puVar4 = (undefined4 *)FUN_0066c194(local_60);
    pcVar7 = (char *)*puVar4;
  } while( true );
}

