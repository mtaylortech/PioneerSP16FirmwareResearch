/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

/* SUPPORTED ANALYST INTERPRETATION; address identity retained. Token checks
   testmode/mscmode/colmode/scriptmode/scriptrecmode. Original source signature is not recovered. */

undefined4 *
sp16_mode_tokens_construct_0065e09c
          (undefined4 *param_1,undefined4 *param_2,undefined4 *param_3,undefined4 *param_4)

{
  char *local_20 [2];
  undefined4 local_18 [2];
  undefined4 local_10 [2];
  
  local_20[0] = (char *)*param_2;
  local_18[0] = *param_3;
  local_10[0] = *param_4;
  *param_1 = 0;
  param_1[1] = 0;
  param_1[2] = 0;
  if (*local_20[0] != '\0') {
    FUN_0065d7c0(param_1,local_20,local_18,local_10);
  }
  return param_1;
}

