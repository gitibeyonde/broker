#!/usr/bin/php5 -q
<?php
error_reporting(E_ALL);
/* Allow the script to hang around waiting for connections. */
set_time_limit(0);
/* Turn on implicit output flushing so we see what we're getting
 * as it comes in. 
 * $unpacked = unpack("Nip/nport", $packed);
echo "IP was ".long2ip($unpacked["ip"])."\n";
echo "Port was ".$unpacked["port"]."\n";
 * 
 * */
ob_implicit_flush();
$address = gethostbyname('broker.ibeyonde.com');
$port = 5020;
if (($sock = socket_create(AF_INET, SOCK_DGRAM, SOL_UDP)) === false) {
    echo "socket_create() failed: reason: " . socket_strerror(socket_last_error()) . "\n";
        exit;
}
if (socket_set_option($sock, SOL_SOCKET, SO_REUSEADDR, 1) == false) {
        echo "socket_sendto() failed: reason: " . socket_strerror(socket_last_error($sock)) . "\n";
        exit;
}
if (socket_bind($sock, 0, intval($port)) === false) {
        echo "socket_bind() failed: reason: " . socket_strerror(socket_last_error($sock)) . "\n";
        exit;
}
echo "address=" . $address . "\n";
$binaddr =  pack('Nn', ip2long($address), intval($port));
$regbuff = "REGISTER:aws:".$binaddr; 
$len = strlen($regbuff);
if (socket_sendto( $sock , $regbuff ,$len ,0 , $address , $port ) == false){
        echo "socket_sendto() failed: reason: " . socket_strerror(socket_last_error($sock)) . "\n";
        exit;
}
$from = '';
if (socket_recvfrom($sock, $buf, 120, 0, $from, $port) == false){
        echo "socket_sendto() failed: reason: " . socket_strerror(socket_last_error($sock)) . "\n";
        exit;
}
echo ">>>$buf " . PHP_EOL;
list($cmd, $data) = explode(":", $buf);
echo "Cmd=".$cmd." and Data=".$data. PHP_EOL;
$array = unpack('N1address/n1port', $data);
print_r($array);
echo "Ip=".long2ip($array['address'])." and Port=".$array['port']. PHP_EOL;

$regbuff = "INITIATE:mac:";
$len = strlen($regbuff);
if (socket_sendto( $sock , $regbuff ,$len ,0 , $address , $port ) == false){
        echo "socket_sendto() failed: reason: " . socket_strerror(socket_last_error($sock)) . "\n";
        exit;
}
echo "INITIATE sent to mac";

$peeraddr='';
$peerport='';
do {
                if (socket_recvfrom($sock, $buf, 120, 0, $from, $port) == false){
                        echo "socket_sendto() failed: reason: " . socket_strerror(socket_last_error($sock)) . "\n";
                        exit;
                }

                echo ">>>$buf " . PHP_EOL;
                list($cmd, $data) = explode(":", $buf);
                echo "Cmd=".$cmd." and Data=".$data. PHP_EOL;

                if ($cmd == 'RINIT'){
                        $array = unpack('N1address/n1port', $data);
                        print_r($array);
                        $peeraddr=long2ip($array['address']);
                        $peerport=$array['port'];
                        echo "Peer Ip=".$peeraddr." and Port=".$peerport. PHP_EOL;
                }
                elseif ($cmd == 'SIZE'){
                        $size = intval($data);
                        echo "File size = ".$size. PHP_EOL;

                        $img='';
                        $remaining = $size;
                        while ($remaining > 0){
                                if (socket_recvfrom($sock, $buf, $remaining, 0, $from, $port) == false){
                                        echo "socket_sendto() failed: reason: " . socket_strerror(socket_last_error($sock)) . "\n";
                                        exit;
                                }
                                $img .= $buf;
                                $remaining -= strlen($buf);
                        }
                }

} while (true);

socket_close($sock);
?>
