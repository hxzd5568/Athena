#!/usr/bin/env bash
#
# File Name: install-agent.sh
# Author: wangchuqing
#
HOME_PATH=$HOME
AGENT_PATH=$HOME_PATH/.iCoding-agent
AGENT_TOKEN=''
CONNECTION_TOKEN=''
REMOTE_VERSION=''
HOST_NAME=`hostname`
USER=`whoami`
http_proxy=''
https_proxy=''
type=2
INSTALL_MODE='ALL'

ls /opt/compiler/gcc-8.2/lib/ld-linux-x86-64.so.2
if (( $? != 0 ))
then
    echo 'Warning:The system is detected to be a non-standard. iCoding recommended to install in Centos6U3 or Centos7U5'
    echo '警告：当前系统非标准镜像，iCoding推荐您使用安全部的标准镜像 Centos6U3 和 Centos7U5'
fi
#中英文双重提示，安全要求
echo 'Warning :Forbid User sensitive operations. such as Modify environment variables and all User related configuration'
echo '警告：建议禁止用户进行敏感操作，例如修改环境变量，和与系统用户有关的配置'
set -e
if [[ ! -f /.dockerenv ]]; then
    type=1
    if [[ $USER == 'root' ]]; then
        echo '*******************************************************************************'
        echo '*      iCoding cannot run with "root", please change to another account.'
        echo '*                禁止在root用户下安装iCoding, 请切换用户安装'
        echo '*******************************************************************************'
        exit 0
    fi
fi
HOST_IP=`hostname -i`
URL='http://icoding.baidu-int.com'
BOS_URL='http://baidu-ide.bj.bcebos.com/platform'
VIRLON_URL='http://baidu-ide.bj.bcebos.com'
if [[ ! -d $AGENT_PATH ]]; then
    mkdir -p $AGENT_PATH
fi
ARCH=$(uname -sm | sed 's/^linux //gi')
case $ARCH in
	x86_64) VSCODE_ARCH="x64";;
	armv7l)
			VSCODE_ARCH="armhf"
		;;
	arm64 | aarch64)
			VSCODE_ARCH="arm64";;
	*)  
        echo '*******************************************************'
        echo '*        Unsupported architecture: '$ARCH''
        echo '*             iCoding暂不支持该体系架构'
        echo '*    e24bf788-cfb5-43a5-b31f-a54826bffbaf##27##'
        echo '*******************************************************'
        exit 0
		;;
esac

# delete old agent
function del_agent() {
    # 删除原进程
    oldagentcount=$(ps -ef | grep 'agent.jar -t '$AGENT_TOKEN | grep -v grep |wc -l)
    oldhostagentcount=$(ps -ef | grep 'host-agent -t '$AGENT_TOKEN | grep -v grep |wc -l)
    supervisecount=$(ps -ef | grep 'status/'$AGENT_TOKEN | grep -v grep |wc -l)
    # 先删除老的守护进程
    if [ 0 == $supervisecount ]; then
        echo "Do not have supervise agent process."
    else
        echo "start kill supervise agent process"
        ps -ef | grep 'status/'$AGENT_TOKEN | grep -v 'grep' | awk '{print $2}' | xargs kill -15
    fi
    if [ 0 == $oldagentcount ]; then
        echo "Do not have old java agent process."
    else
        echo "start kill old java agent process"
        ps -ef | grep 'agent.jar -t '$AGENT_TOKEN | grep -v 'grep' | awk '{print $2}' | xargs kill -15
        # 删除.bash_profile的agent自启
        if [[ -f ~/.bash_profile ]]; then
            agent_profile=0
            cat ~/.bash_profile | grep $AGENT_TOKEN | grep -v 'grep' || agent_profile=1
            if [[ "$agent_profile" == "0" ]]; then
                startLine=$(sed -n "/ps aux|grep $AGENT_TOKEN/=" ~/.bash_profile)
                let endLine="startLine + 3"
                sed -i $startLine','$endLine'd' ~/.bash_profile
            fi
        elif [[ -f ~/.profile ]]; then
            agent_profile=0
            cat ~/.profile | grep $AGENT_TOKEN | grep -v 'grep' || agent_profile=1
            if [[ "$agent_profile" == "0" ]]; then
                startLine=$(sed -n "/ps aux|grep $AGENT_TOKEN/=" ~/.profile)
                let endLine="startLine + 3"
                sed -i $startLine','$endLine'd' ~/.profile
            fi
        fi
    fi
    if [ 0 == $oldhostagentcount ]; then
        echo "Do not have old host agent process."
    else
        echo "start kill old host agent process"
        ps -ef | grep 'host-agent -t '$AGENT_TOKEN | grep -v 'grep' | awk '{print $2}' | xargs kill -15
        sleep 3
    fi
}

# start the agent
function start_agent() {    
    # arm64 and armhf arch compatibility
    case $VSCODE_ARCH in
	x64) 
        HOST_AGENT_PATH=$BOS_URL/package/host-agent/amd64/host-agent;;

	arm64)
        HOST_AGENT_PATH=$BOS_URL/package/host-agent/arm64/host-agent;;
    esac
    # Download the agent
    if [[ ! -f $AGENT_PATH/host-agent ]]; then
        wget -O $AGENT_PATH/host-agent $HOST_AGENT_PATH --no-check-certificate && chmod 755 $AGENT_PATH/host-agent
        if (( $? != 0 ))
        then
            echo '****************************************************************************'
            echo '*            Download host-agent failed. Please checkout network'
            echo '*               agent下载失败，请尝试手动执行以下命令检查网络问题'
            echo '*   wget https://baidu-ide.bj.bcebos.com/platform/package/host-agent/amd64/host-agent'
            echo '****************************************************************************'
            exit 0
        else
            echo "Download host-agent complete."
        fi
    fi
    # Run the agent
    cd $AGENT_PATH
    nohup $AGENT_PATH/host-agent -t $AGENT_TOKEN -s $URL > /dev/null 2>&1 &
    if (( $? != 0 ))
    then
        echo "***************************************************************************************************"
        echo "*                                    Host-Agent start fail!"
        echo "*                                      Host-Agent启动失败"
        echo "***************************************************************************************************"
        exit 0
    else
        sleep 3
        count=$(ps -ef |grep "host-agent -t $AGENT_TOKEN" |grep -v "grep" |wc -l)
        if [ 0 == $count ]; then
            echo "***************************************************************************************************"
            echo "*                                    Host-Agent start fail!"
            echo "*                                      Host-Agent启动失败"
            echo "***************************************************************************************************"
            exit 0
        else
            echo "Start the agent success."
        fi
	fi
} 

# check whether the agent had registered
function check_agent_register() {
    header='Content-Type: application/x-www-form-urlencoded'
    porturl=$URL'/platform/agent/registeragent'
    CURL_RES=$(curl -H "$header" -XPOST -d "gtoken=$AGENT_TOKEN&host=$HOST_NAME&ip=$HOST_IP&check=$1&remotePort=$2&webviewPort=$3&path=$HOME_PATH&version=$REMOTE_VERSION&type=$type&sourcePort=$PORT&agent_type=host-agent" $porturl)
    code=`echo $CURL_RES|sed -n 's/.*"code":\([01]\).*/\1/p'`
    msg=`echo $CURL_RES|sed 's/.*"message":"//;s/".*//'`
    if [[ $code -eq 1 ]]
    then
        echo '****************************************************************************'
        echo "*    $msg"
        echo '*                         Register failed, exit.'
        echo '*                     注册失败,请在FAQ中搜索错误关键词排查'
        echo '****************************************************************************'
        exit 0
    else
        echo 'Register success. start installing remote-server...'
    fi
}

# install remote server
function install_remote_server() {
    #Download remote install script
    INSTALL_SH_PATH=$AGENT_PATH/install-remote.sh
    if [[ -d "$INSTALL_SH_PATH" ]]; then
        rm -rf $INSTALL_SH_PATH
    fi
    wget -O $INSTALL_SH_PATH $BOS_URL/script/install-remote.sh --no-check-certificate
    if (( $? != 0 ))
    then
        echo "Download remote server install script failed."
        exit 0
    else
        echo "Download complete."
    fi
    # Start the remote server
    bash $INSTALL_SH_PATH $REMOTE_VERSION $CONNECTION_TOKEN $PORT $AGENT_TOKEN
    if (( $? != 0 ))
    then
        echo "Start remote server install scpipt failed."
        exit 0
    fi
    VSCODE_AGENT_FOLDER=$HOME_PATH/.vscode-server
    VSCH_LOGFILE="$VSCODE_AGENT_FOLDER/.$REMOTE_VERSION-$CONNECTION_TOKEN.log"
    stopTime=$((SECONDS+5))
    while (($SECONDS < $stopTime))
    do
        PROCESS_PORT=$(cat "$VSCH_LOGFILE" | grep -a -E 'Extension host agent listening on [0-9]+' | grep -v grep | grep -o -E '[0-9]+')
        if [[ $PROCESS_PORT != '' ]]
        then
            break
        fi
        echo "Waiting for server log..."
        sleep .5
    done
    PROCESS_PORT=$(cat "$VSCH_LOGFILE" | grep -a -E 'Extension host agent listening on [0-9]+' | grep -v grep | grep -o -E '[0-9]+')
    if [[ -z $PROCESS_PORT ]]
    then
        echo "Server did not start successfully. Full server log >>>"
        cat $VSCH_LOGFILE
        exit 0
    else
        echo "Server start successfully."
    fi
    check_agent_register false $PORT 0
}

# install plugin
function install_plugin() {
    #Download plugin install script
    INSTALL_PLUGIN_PATH=$AGENT_PATH/install-plugin.sh
    INSTALL_VIRLON_PATH=$AGENT_PATH/install.sh
    if [[ -d "$INSTALL_PLUGIN_PATH" ]]; then
        rm -rf $INSTALL_PLUGIN_PATH
    fi
    wget -O $INSTALL_PLUGIN_PATH $BOS_URL/script/install-plugin.sh --no-check-certificate
    bash $INSTALL_PLUGIN_PATH icafe $AGENT_TOKEN "false"
    bash $INSTALL_PLUGIN_PATH virlon $AGENT_TOKEN "false"
    bash $INSTALL_PLUGIN_PATH comate $AGENT_TOKEN "false"
    bash $INSTALL_PLUGIN_PATH icode-code-review $AGENT_TOKEN "false"
    bash $INSTALL_PLUGIN_PATH code-style $AGENT_TOKEN "false"
    bash $INSTALL_PLUGIN_PATH icode-code-search $AGENT_TOKEN "false"
    bash $INSTALL_PLUGIN_PATH file-download $AGENT_TOKEN "false"
    wget -O $INSTALL_VIRLON_PATH $VIRLON_URL/virlon/scripts/install.sh --no-check-certificate
    bash $INSTALL_VIRLON_PATH
}

function chose_port() {
    # 若无指定启动端口号则随机30000-50000
    if [[ $PORT ]]
    then
        echo "vscode server port is $PORT"
        return
    else
        while ((1))
        do
            PORT=$(($RANDOM%20000+30000))
            pid=`/usr/sbin/lsof -i :$PORT|grep -v "PID" | awk '{print $2}'`
            if [ "$pid" != "" ]
            then
                echo "port: $PORT is in use"
            else
                echo "vscode server port is $PORT"
                return
            fi
        done
    fi
}

# -g agenttoken -c connectiontoken -v remote version -p port
function main() {
    while getopts "p:v:c:g:m:" arg
    do
    case $arg in
        p) PORT=$OPTARG;;
        v) REMOTE_VERSION=$OPTARG;;
        c) CONNECTION_TOKEN=$OPTARG;;
        g) AGENT_TOKEN=$OPTARG;;
        m) INSTALL_MODE=$OPTARG;;
    esac
    done
    if [ -z "$REMOTE_VERSION" ] || [ -z "$CONNECTION_TOKEN" ] || [ -z "$AGENT_TOKEN" ]
    then
        echo 'Missing parameters!'
        exit 0
    fi
    del_agent
    check_agent_register true
    start_agent
    chose_port
    install_remote_server
    echo '========Install and register agent success!!=======' 
    if [ "$INSTALL_MODE" != "LITE" ]
    then 
        install_plugin
    fi
}
main "$@"%                                                                      xiazichao@MacBook-Pro ~ % pwd
/Users/xiazichao
xiazichao@MacBook-Pro ~ % cd Downloads 
xiazichao@MacBook-Pro Downloads % curl http://baidu-ide.bj.bcebos.com/platform/script/host-script/install-agent.sh
#!/usr/bin/env bash
#
# File Name: install-agent.sh
# Author: wangchuqing
#
HOME_PATH=$HOME
AGENT_PATH=$HOME_PATH/.iCoding-agent
AGENT_TOKEN=''
CONNECTION_TOKEN=''
REMOTE_VERSION=''
HOST_NAME=`hostname`
USER=`whoami`
http_proxy=''
https_proxy=''
type=2
INSTALL_MODE='ALL'

ls /opt/compiler/gcc-8.2/lib/ld-linux-x86-64.so.2
if (( $? != 0 ))
then
    echo 'Warning:The system is detected to be a non-standard. iCoding recommended to install in Centos6U3 or Centos7U5'
    echo '警告：当前系统非标准镜像，iCoding推荐您使用安全部的标准镜像 Centos6U3 和 Centos7U5'
fi
#中英文双重提示，安全要求
echo 'Warning :Forbid User sensitive operations. such as Modify environment variables and all User related configuration'
echo '警告：建议禁止用户进行敏感操作，例如修改环境变量，和与系统用户有关的配置'
set -e
if [[ ! -f /.dockerenv ]]; then
    type=1
    if [[ $USER == 'root' ]]; then
        echo '*******************************************************************************'
        echo '*      iCoding cannot run with "root", please change to another account.'
        echo '*                禁止在root用户下安装iCoding, 请切换用户安装'
        echo '*******************************************************************************'
        exit 0
    fi
fi
HOST_IP=`hostname -i`
URL='http://icoding.baidu-int.com'
BOS_URL='http://baidu-ide.bj.bcebos.com/platform'
VIRLON_URL='http://baidu-ide.bj.bcebos.com'
if [[ ! -d $AGENT_PATH ]]; then
    mkdir -p $AGENT_PATH
fi
ARCH=$(uname -sm | sed 's/^linux //gi')
case $ARCH in
	x86_64) VSCODE_ARCH="x64";;
	armv7l)
			VSCODE_ARCH="armhf"
		;;
	arm64 | aarch64)
			VSCODE_ARCH="arm64";;
	*)  
        echo '*******************************************************'
        echo '*        Unsupported architecture: '$ARCH''
        echo '*             iCoding暂不支持该体系架构'
        echo '*    e24bf788-cfb5-43a5-b31f-a54826bffbaf##27##'
        echo '*******************************************************'
        exit 0
		;;
esac

# delete old agent
function del_agent() {
    # 删除原进程
    oldagentcount=$(ps -ef | grep 'agent.jar -t '$AGENT_TOKEN | grep -v grep |wc -l)
    oldhostagentcount=$(ps -ef | grep 'host-agent -t '$AGENT_TOKEN | grep -v grep |wc -l)
    supervisecount=$(ps -ef | grep 'status/'$AGENT_TOKEN | grep -v grep |wc -l)
    # 先删除老的守护进程
    if [ 0 == $supervisecount ]; then
        echo "Do not have supervise agent process."
    else
        echo "start kill supervise agent process"
        ps -ef | grep 'status/'$AGENT_TOKEN | grep -v 'grep' | awk '{print $2}' | xargs kill -15
    fi
    if [ 0 == $oldagentcount ]; then
        echo "Do not have old java agent process."
    else
        echo "start kill old java agent process"
        ps -ef | grep 'agent.jar -t '$AGENT_TOKEN | grep -v 'grep' | awk '{print $2}' | xargs kill -15
        # 删除.bash_profile的agent自启
        if [[ -f ~/.bash_profile ]]; then
            agent_profile=0
            cat ~/.bash_profile | grep $AGENT_TOKEN | grep -v 'grep' || agent_profile=1
            if [[ "$agent_profile" == "0" ]]; then
                startLine=$(sed -n "/ps aux|grep $AGENT_TOKEN/=" ~/.bash_profile)
                let endLine="startLine + 3"
                sed -i $startLine','$endLine'd' ~/.bash_profile
            fi
        elif [[ -f ~/.profile ]]; then
            agent_profile=0
            cat ~/.profile | grep $AGENT_TOKEN | grep -v 'grep' || agent_profile=1
            if [[ "$agent_profile" == "0" ]]; then
                startLine=$(sed -n "/ps aux|grep $AGENT_TOKEN/=" ~/.profile)
                let endLine="startLine + 3"
                sed -i $startLine','$endLine'd' ~/.profile
            fi
        fi
    fi
    if [ 0 == $oldhostagentcount ]; then
        echo "Do not have old host agent process."
    else
        echo "start kill old host agent process"
        ps -ef | grep 'host-agent -t '$AGENT_TOKEN | grep -v 'grep' | awk '{print $2}' | xargs kill -15
        sleep 3
    fi
}

# start the agent
function start_agent() {    
    # arm64 and armhf arch compatibility
    case $VSCODE_ARCH in
	x64) 
        HOST_AGENT_PATH=$BOS_URL/package/host-agent/amd64/host-agent;;

	arm64)
        HOST_AGENT_PATH=$BOS_URL/package/host-agent/arm64/host-agent;;
    esac
    # Download the agent
    if [[ ! -f $AGENT_PATH/host-agent ]]; then
        wget -O $AGENT_PATH/host-agent $HOST_AGENT_PATH --no-check-certificate && chmod 755 $AGENT_PATH/host-agent
        if (( $? != 0 ))
        then
            echo '****************************************************************************'
            echo '*            Download host-agent failed. Please checkout network'
            echo '*               agent下载失败，请尝试手动执行以下命令检查网络问题'
            echo '*   wget https://baidu-ide.bj.bcebos.com/platform/package/host-agent/amd64/host-agent'
            echo '****************************************************************************'
            exit 0
        else
            echo "Download host-agent complete."
        fi
    fi
    # Run the agent
    cd $AGENT_PATH
    nohup $AGENT_PATH/host-agent -t $AGENT_TOKEN -s $URL > /dev/null 2>&1 &
    if (( $? != 0 ))
    then
        echo "***************************************************************************************************"
        echo "*                                    Host-Agent start fail!"
        echo "*                                      Host-Agent启动失败"
        echo "***************************************************************************************************"
        exit 0
    else
        sleep 3
        count=$(ps -ef |grep "host-agent -t $AGENT_TOKEN" |grep -v "grep" |wc -l)
        if [ 0 == $count ]; then
            echo "***************************************************************************************************"
            echo "*                                    Host-Agent start fail!"
            echo "*                                      Host-Agent启动失败"
            echo "***************************************************************************************************"
            exit 0
        else
            echo "Start the agent success."
        fi
	fi
} 

# check whether the agent had registered
function check_agent_register() {
    header='Content-Type: application/x-www-form-urlencoded'
    porturl=$URL'/platform/agent/registeragent'
    CURL_RES=$(curl -H "$header" -XPOST -d "gtoken=$AGENT_TOKEN&host=$HOST_NAME&ip=$HOST_IP&check=$1&remotePort=$2&webviewPort=$3&path=$HOME_PATH&version=$REMOTE_VERSION&type=$type&sourcePort=$PORT&agent_type=host-agent" $porturl)
    code=`echo $CURL_RES|sed -n 's/.*"code":\([01]\).*/\1/p'`
    msg=`echo $CURL_RES|sed 's/.*"message":"//;s/".*//'`
    if [[ $code -eq 1 ]]
    then
        echo '****************************************************************************'
        echo "*    $msg"
        echo '*                         Register failed, exit.'
        echo '*                     注册失败,请在FAQ中搜索错误关键词排查'
        echo '****************************************************************************'
        exit 0
    else
        echo 'Register success. start installing remote-server...'
    fi
}

# install remote server
function install_remote_server() {
    #Download remote install script
    INSTALL_SH_PATH=$AGENT_PATH/install-remote.sh
    if [[ -d "$INSTALL_SH_PATH" ]]; then
        rm -rf $INSTALL_SH_PATH
    fi
    wget -O $INSTALL_SH_PATH $BOS_URL/script/install-remote.sh --no-check-certificate
    if (( $? != 0 ))
    then
        echo "Download remote server install script failed."
        exit 0
    else
        echo "Download complete."
    fi
    # Start the remote server
    bash $INSTALL_SH_PATH $REMOTE_VERSION $CONNECTION_TOKEN $PORT $AGENT_TOKEN
    if (( $? != 0 ))
    then
        echo "Start remote server install scpipt failed."
        exit 0
    fi
    VSCODE_AGENT_FOLDER=$HOME_PATH/.vscode-server
    VSCH_LOGFILE="$VSCODE_AGENT_FOLDER/.$REMOTE_VERSION-$CONNECTION_TOKEN.log"
    stopTime=$((SECONDS+5))
    while (($SECONDS < $stopTime))
    do
        PROCESS_PORT=$(cat "$VSCH_LOGFILE" | grep -a -E 'Extension host agent listening on [0-9]+' | grep -v grep | grep -o -E '[0-9]+')
        if [[ $PROCESS_PORT != '' ]]
        then
            break
        fi
        echo "Waiting for server log..."
        sleep .5
    done
    PROCESS_PORT=$(cat "$VSCH_LOGFILE" | grep -a -E 'Extension host agent listening on [0-9]+' | grep -v grep | grep -o -E '[0-9]+')
    if [[ -z $PROCESS_PORT ]]
    then
        echo "Server did not start successfully. Full server log >>>"
        cat $VSCH_LOGFILE
        exit 0
    else
        echo "Server start successfully."
    fi
    check_agent_register false $PORT 0
}

# install plugin
function install_plugin() {
    #Download plugin install script
    INSTALL_PLUGIN_PATH=$AGENT_PATH/install-plugin.sh
    INSTALL_VIRLON_PATH=$AGENT_PATH/install.sh
    if [[ -d "$INSTALL_PLUGIN_PATH" ]]; then
        rm -rf $INSTALL_PLUGIN_PATH
    fi
    wget -O $INSTALL_PLUGIN_PATH $BOS_URL/script/install-plugin.sh --no-check-certificate
    bash $INSTALL_PLUGIN_PATH icafe $AGENT_TOKEN "false"
    bash $INSTALL_PLUGIN_PATH virlon $AGENT_TOKEN "false"
    bash $INSTALL_PLUGIN_PATH comate $AGENT_TOKEN "false"
    bash $INSTALL_PLUGIN_PATH icode-code-review $AGENT_TOKEN "false"
    bash $INSTALL_PLUGIN_PATH code-style $AGENT_TOKEN "false"
    bash $INSTALL_PLUGIN_PATH icode-code-search $AGENT_TOKEN "false"
    bash $INSTALL_PLUGIN_PATH file-download $AGENT_TOKEN "false"
    wget -O $INSTALL_VIRLON_PATH $VIRLON_URL/virlon/scripts/install.sh --no-check-certificate
    bash $INSTALL_VIRLON_PATH
}

function chose_port() {
    # 若无指定启动端口号则随机30000-50000
    if [[ $PORT ]]
    then
        echo "vscode server port is $PORT"
        return
    else
        while ((1))
        do
            PORT=$(($RANDOM%20000+30000))
            pid=`/usr/sbin/lsof -i :$PORT|grep -v "PID" | awk '{print $2}'`
            if [ "$pid" != "" ]
            then
                echo "port: $PORT is in use"
            else
                echo "vscode server port is $PORT"
                return
            fi
        done
    fi
}

# -g agenttoken -c connectiontoken -v remote version -p port
function main() {
    while getopts "p:v:c:g:m:" arg
    do
    case $arg in
        p) PORT=$OPTARG;;
        v) REMOTE_VERSION=$OPTARG;;
        c) CONNECTION_TOKEN=$OPTARG;;
        g) AGENT_TOKEN=$OPTARG;;
        m) INSTALL_MODE=$OPTARG;;
    esac
    done
    if [ -z "$REMOTE_VERSION" ] || [ -z "$CONNECTION_TOKEN" ] || [ -z "$AGENT_TOKEN" ]
    then
        echo 'Missing parameters!'
        exit 0
    fi
    del_agent
    check_agent_register true
    start_agent
    chose_port
    install_remote_server
    echo '========Install and register agent success!!=======' 
    if [ "$INSTALL_MODE" != "LITE" ]
    then 
        install_plugin
    fi
}
