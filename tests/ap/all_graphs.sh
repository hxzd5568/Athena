#!/bin/bash

# 定义变量
test_dir="/framework/e2e/PaddleLT_new/layerE2Ecase/matmul-related-subgraphs/"
log_root="/work/Paddle/Athena/tests/ap/ap_matmul_graphs/"
dir_name="/work/PaddleTest/"
shell_script="/work/Paddle/Athena/"
priority_cases_str="01f387927f59470e4d98ffd80183e55c,05958b7bce36d4f49a9c58949af92e5f,0b1e9e1811c2caaab597bbc30dc64f15,1300635db023d0d4fc989f55acaeb68c,258da0d281b03ff3e9d485112427b2e0,30c6df92480843563881b3547ef00a70,32b3c2445138bb176126ec49ce12b920,360f44fe695c9d2d2bb3e0e2b0dec8ac,3cbeaa359cf1f5213ef9b53e84991175,4745af600b1a1a2e571860b739abdf51,51ccf25fcaf79fe57807277986c95abe,5205b522fb5d36186a4e1a2fe841d888,5a7a71c544c3f6d7f503189e31cb8224,5be1aef63a75b06b9d4607f14874dcca,623fe5f470e8682954dc6ba1d25405a7,6241136fcffe5083b24443ec6018217e,63d9162b25876e4243c844dd2712cba8,64902819a5b144aa518dcc1b62619713,6585ddf0dfb3b8aca54220e05c760d87,6739319539b71905d9cd2fa6b6e69993,6df4c95df0beee147bade3fea12cbfc8,6e8ea012e0a6cd1cd4539486497f5a88,6fd72e19394a8db2c8fed04b1fa01752,7b6c128e41453ea52c85c02b7c3a9d3a,801916bb28c4ae55391799323a72e97f,833cb0c8a48c02f8c845749b53866b79,8b7e7925cc84a4c14bc8de33f406b0f7,94f503573a1ce7dc15457fe473995d31,9642da331ae02f289778014a1edcbdc1,9683464a1fe31aad86eccf1a85acb73c,9acfbcce718bf2b38fa02cdf5ff38910,9d9701ea5a62c96bc6c62b330e7e8468,9dec831d26e88185dcb1986bb8adc440,9e11e7abbbff9e92aba537a6b1638525,9fa97bc70a143d3d5b9582c1ba2d4272,a203a286f7c0b99d676299abbb619170,a4d35b423347cdc00e1644c76ee320c4,a58889e1be5e32da7c6fa77c0be9195c,a698d689d224203b88f6ecbdbb7a3fe1,a6b0ed75b1eb7f1a1f3759d242d1b87a,aa462034c34ecd897f35e22b2b9cf9f8,aec45446b61a083b6a4e014a04e6f009,af3e782a6a41b342a6c59d9a853347d4,b142765b86967084713a3e8745ffe619,b3c116f98f26b175738166e7645eb869,b3fde09b1620ec2e4fb965ff33b2a483,b4cf9857f6257675d7c2bf06e211b638,b7c8f4e6dcc0c46d1f776e8d8a95bad3,b99897a41050399f9764ace87b218eb3,bbbdf176b7ed6336c10f5c2ca476b418,be6b8412cfb95999692e178d0aa8695c,be734570fe5aeb67473c9283d555538a,c0195ecb1a43c55192478a6d05ee7e58,c855449d99a4d85c32c87cfb9e5e5b1e,c880f59a081a5e304fcaee03a373ea82,ce1267a5f57b3040514d414764bc9017,d2b60d61247483ca217400d03e27ce02,d41e4c8cbf723cad95ca49bb968a820d,d737d027e82af5a5d51dc3f0cbf99f53,e040cb6ba8ddc57e3b9da4773ac8f08b,e173ac7061eebb7935c1efc78338b97a,e2aab794d893c2b993becce389b47b51,e32419e9e757c11bb18dea11e052aec9,ea9eca45d1609de210a9f9bf55feb079,ebfbe603265d50f8afbb5029d9435fee,f4ede8a0f94c5daa2ad572d969d5d311,f6fd6824ed9f46608b1946e3c38878ac,f8136c4d286b6bc602ca932ac65d9e0a,fbf699eec701872c7fd286a2a6821bc1,fc4365802da42bfb7e905cb00f5de671,fcf544c4f0f0189f51c2edd76ca03f02,fef08e9fd2d93fe75aaeb0b4cdc76953"
priority_cases_str="9683464a1fe31aad86eccf1a85acb73c,e040cb6ba8ddc57e3b9da4773ac8f08b,801916bb28c4ae55391799323a72e97f,fbf699eec701872c7fd286a2a6821bc1,be734570fe5aeb67473c9283d555538a,af3e782a6a41b342a6c59d9a853347d4,5205b522fb5d36186a4e1a2fe841d888,c0195ecb1a43c55192478a6d05ee7e58,9fa97bc70a143d3d5b9582c1ba2d4272,6e8ea012e0a6cd1cd4539486497f5a88,360f44fe695c9d2d2bb3e0e2b0dec8ac,aa462034c34ecd897f35e22b2b9cf9f8,8b7e7925cc84a4c14bc8de33f406b0f7,9d9701ea5a62c96bc6c62b330e7e8468,e32419e9e757c11bb18dea11e052aec9,9642da331ae02f289778014a1edcbdc1,833cb0c8a48c02f8c845749b53866b79,3cbeaa359cf1f5213ef9b53e84991175,f4ede8a0f94c5daa2ad572d969d5d311,b3fde09b1620ec2e4fb965ff33b2a483,01f387927f59470e4d98ffd80183e55c,5a7a71c544c3f6d7f503189e31cb8224,9acfbcce718bf2b38fa02cdf5ff38910,05958b7bce36d4f49a9c58949af92e5f,e173ac7061eebb7935c1efc78338b97a,e2aab794d893c2b993becce389b47b51,d41e4c8cbf723cad95ca49bb968a820d,623fe5f470e8682954dc6ba1d25405a7,b142765b86967084713a3e8745ffe619,6739319539b71905d9cd2fa6b6e69993,fef08e9fd2d93fe75aaeb0b4cdc76953,9dec831d26e88185dcb1986bb8adc440,32b3c2445138bb176126ec49ce12b920,7b6c128e41453ea52c85c02b7c3a9d3a,c880f59a081a5e304fcaee03a373ea82,a698d689d224203b88f6ecbdbb7a3fe1,bbbdf176b7ed6336c10f5c2ca476b418,c855449d99a4d85c32c87cfb9e5e5b1e,fcf544c4f0f0189f51c2edd76ca03f02,a4d35b423347cdc00e1644c76ee320c4,d2b60d61247483ca217400d03e27ce02,ea9eca45d1609de210a9f9bf55feb079,6df4c95df0beee147bade3fea12cbfc8,1300635db023d0d4fc989f55acaeb68c,fc4365802da42bfb7e905cb00f5de671,64902819a5b144aa518dcc1b62619713,d737d027e82af5a5d51dc3f0cbf99f53"
priority_cases=$(echo "$priority_cases_str" | tr ',' '\n' | sed 's/^/test_sequence_/; s/$/_0/')
gpu_id=2

# 创建日志目录
hash_code=$(date +"%Y-%m-%d_%H:%M:%S")
log_dir="$log_root/$hash_code"
mkdir -p "$log_dir"

# 检查路径是否存在
if [ ! -d "$dir_name" ]; then
  echo "<Path Error> : Please Initialize the \`dir_name\` variable with the location of PaddleTest."
  exit 1
fi

if [ ! -d "$shell_script" ]; then
  echo "<Path Error> : Please Initialize the \`shell_script\` variable with the location of Athena."
  exit 1
fi

# 测试所有图
test_all_graphs() {
  local log_dir=$1
  local test_all_case=$2

  for file_name in $(ls "$dir_name$test_dir"); do
    # 提取文件名中的序列号
    file_seq_num=$(echo "$file_name" | sed 's/\.py$//')
    
    # 跳过非优先级用例
    if ! echo "$priority_cases" | grep -q "$file_seq_num"; then
      echo "Skipping non-phase1-2 case $file_seq_num"
      continue
    fi

    # 根据测试类型过滤文件
    test_case_type=".py"
    if [ "$test_all_case" != "true" ]; then
      test_case_type="_0.py"
    fi

    if [[ "$file_name" == *"$test_case_type" ]]; then
      for i in {0..2}; do
        file_id=$((i + 1))
        cmd=("bash" "$shell_script/tests/ap/auto$file_id.sh" "$file_seq_num" "$log_dir" "$gpu_id")
        
        # 执行命令并捕获错误
        time_begin=$(date +%s)
        if timeout 100 "${cmd[@]}"; then
          time_end=$(date +%s)
          duration=$((time_end - time_begin))
          echo "Case $file_seq_num finished in $duration seconds." >> "$log_dir/alog.txt"
        else
          echo "Error or timeout detected in case $file_seq_num." >> "$log_dir/alog.txt"
        fi

        sleep 3
      done

      # 更新 GPU ID
      gpu_id=$((gpu_id + 1))
      if [ "$gpu_id" -eq 4 ]; then
        gpu_id=2
      fi

      sleep 5
    fi
  done
}

# 计算成功率
cal_successful_rate() {
  local log_dir=$1
  ap_num=0
  sum_num=0

  for file_name in $(ls "$log_dir"); do
    if [[ "$file_name" == *.txt ]]; then
      fusion_num=$(grep -o '"pd_op.ap' "$log_dir/$file_name" | wc -l)
      if [ "$fusion_num" -ge 1 ]; then
        ap_num=$((ap_num + 1))
        echo "$fusion_num AP fusion found in $file_name"
      fi

      matmul_num=$(grep -o '"pd_op.matmul' "$log_dir/$file_name" | wc -l)
      if [ "$matmul_num" -lt 1 ]; then
        echo "No matmul found in $file_name"
      else
        sum_num=$((sum_num + 1))
      fi
    fi
  done

  echo "total: $sum_num, containing ap fusion: $ap_num, ap coverage rate: $(echo "$ap_num / $sum_num" | bc -l)"
}

# 主程序
test_all_graphs "$log_dir" "false"
# cal_successful_rate "$log_dir"