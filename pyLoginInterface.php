<?php
	//Hello, python! (simple quick and dirty login interface with semi-advanced hashing algorithm)
	if(isset($_POST['python']) && $_POST['python'] == 1)
	{
		//Some house cleaning
		header('Content-Type: text/plain');
		ini_set('session.use_cookies', 0);
		ini_set('session.use_trans_sid', 1);
		
		if(!filter_var($_SERVER['REMOTE_ADDR'], FILTER_VALIDATE_IP))
		{
			header("HTTP/1.0 404 Not Found");
			echo 'BadRequest';
			exit;
		}
		
		else $IP = $_SERVER['REMOTE_ADDR'];
		
		if(isset($_POST['SID'])) session_id(filter_var($_POST['SID'], FILTER_SANITIZE_STRING));
		session_start();
		
		//Maintenance mode (server offline when true)
		$_SESSION['MAINTENANCE_MODE'] = false;
		if($_SESSION['MAINTENANCE_MODE'])
		{
			echo 'MAINTENANCE_MODE';
			return;
		}
		
		//Possible TODO - extra protection against session hijacking by using the random challenge as a parameter
		//(and regenerating every time we talk, and then requesting the original + the latest as a sort of salt)
		
		//If they're asking us for a random encryption code...
		if(isset($_POST['nec']) && $_POST['nec'] == 1)
		{
			$_SESSION['PYTHON']['challenge'] = sha1(time().date('dmy')).rand(1, 10000);
			echo $_SESSION['PYTHON']['challenge'].'@'.session_id();
		}
		
		//If they're trying to log in (or just requesting some user data)...
		else if(!empty($_POST['SID']))
		{
			if(!empty($_POST['u']) && !empty($_POST['p']))
			{
				//Connect to the MySQL server
				$dbc = mysqli_connect('mhousepython.db.4619325.hostedresource.com', '[REMOVED]', '[REMOVED]', '[REMOVED]');
				$r = isset($_POST['type']) && $_POST['type'] == 'reg';
				
				//Grab their IP address and the current execution time
				$r_timestamp = gmdate("Y-m-d H:i:s", time());
				list($ipv0, $ipv1, $ipv2, $ipv3) = explode('.', $IP);
				
				//Grab how many times this IP has attempted to log in/register in the past hour
				$row = mysqli_fetch_array(mysqli_query($dbc, "SELECT COUNT(*) count FROM history WHERE active = '1' AND action = '".($r ? 'g' : 'c')."' AND CONCAT(ipv0, '.', ipv1, '.', ipv2, '.', ipv3) = '$IP' AND entry_date + INTERVAL ".($r ? 72 : 1)." HOUR >= '$r_timestamp'"));
						
				//Utoh, this IP's a bad boy!
				if($row['count'] >= ($r ? 3 : 5))
				{
					mysqli_query($dbc, "INSERT INTO history (action, ipv0, ipv1, ipv2, ipv3, entry_date) VALUES ('".($r ? 'h' : 'd')."', $ipv0, $ipv1, $ipv2, $ipv3, '$r_timestamp')");
					echo 'RateLimited';
				}
				
				else
				{
					
					//Escape the username and password
					$post['username'] = mysqli_real_escape_string($dbc, preg_replace("/[^0-9_a-zA-Z]/i", '', $_POST['u']));
					$post['password'] = mysqli_real_escape_string($dbc, $_POST['p']);
					
					//Automatically fail if the password doesn't match the escaped password
					if($_POST['p'] != $post['password'] || $_POST['u'] != $post['username'] || strlen($post['username']) > 100 || strlen($post['password']) > 100 || strlen($post['username']) < 4)
					{
						if(!$r) mysqli_query($dbc, "INSERT INTO history (action, ipv0, ipv1, ipv2, ipv3, entry_date) VALUES ('a', $ipv0, $ipv1, $ipv2, $ipv3, '$r_timestamp')");
						echo 'Malformed';
					}
					
					else if(isset($_POST['type']))
					{
						//Check the supplied credentials against our database (the meat and potatoes!)
						if($r) $result = mysqli_query($dbc, "SELECT username FROM users WHERE username = '$post[username]'");
						else $result = mysqli_query($dbc, 'SELECT '.($_POST['type'] == 'lin'?'username':'*').' FROM `users` WHERE SHA1(CONCAT(\''.substr($_SESSION['PYTHON']['challenge'], 0, 20).'\', username, \''.substr($_SESSION['PYTHON']['challenge'], 20, 20).'\')) = \''.$post['username'].'\' AND SHA1(CONCAT(\''.substr($_SESSION['PYTHON']['challenge'], 0, 20).'\', password, \''.substr($_SESSION['PYTHON']['challenge'], 20, 20).'\')) = \''.$post['password'].'\' LIMIT 1');
						$row = mysqli_fetch_array($result);
						
						//If the username(+password) matched
						if(mysqli_num_rows($result) == 1)
						{
							//If they're asking for user data...
							if($_POST['type'] == 'dat')
							{
								$new_array = array('logout_warning' => 0, 'login_warning' => 0);
								
								//See if they've logged in without logging out
								$rows = mysqli_fetch_array(mysqli_query($dbc, "SELECT action AS e FROM history WHERE active = '1' AND action IN ('b', 'e') AND CONCAT(ipv0, '.', ipv1, '.', ipv2, '.', ipv3) = '$IP' ORDER BY entry_id DESC LIMIT 1, 1"));
								
								//See if they've logged in without logging out
								$row2 = mysqli_fetch_array(mysqli_query($dbc, "SELECT extra AS extra FROM history WHERE active = '1' AND action = 'f' AND CONCAT(ipv0, '.', ipv1, '.', ipv2, '.', ipv3) = '$IP' LIMIT 1"));
								
								if(isset($rows['e']) && $rows['e'] == 'b') $new_array['logout_warning'] = 1;
								if(isset($row2['extra']) && !empty($row2['extra'])) $new_array['login_warning'] = $row2['extra'];
								echo json_encode(array_merge($row, $new_array));
							}
							
							//If they're asking to log out
							else if($_POST['type'] == 'out')
							{
								//Bye! :3
								mysqli_query($dbc, "UPDATE users SET connected = 'F' WHERE username = '$row[username]' LIMIT 1");
								mysqli_query($dbc, "INSERT INTO history (action, ipv0, ipv1, ipv2, ipv3, entry_date, extra) VALUES ('e', $ipv0, $ipv1, $ipv2, $ipv3, '$r_timestamp', '$row[username]')");
			
								$_SESSION['PYTHON'] = array();
								unset($_SESSION['PYTHON']);
								
								//Stomp some bugs...
								session_regenerate_id();
								session_destroy();
								echo 'Goodbye';
							}
							
							//Otherwise, they're trying to log in
							else if($_POST['type'] == 'lin')
							{
								mysqli_query($dbc, "UPDATE history SET active = '0' WHERE action = 'f' AND active = '1' AND CONCAT(ipv0, '.', ipv1, '.', ipv2, '.', ipv3) = '$IP'");
								
								//See if others tried to log into their account, and if so, report it!
								$rows = mysqli_fetch_array(mysqli_query($dbc, "SELECT COUNT(*) as c, (SELECT COUNT(*) FROM (SELECT DISTINCT ipv0, ipv1, ipv2, ipv3 FROM history WHERE extra = '{$row['username']}' AND active = '1' AND action = 'c' GROUP BY ipv0, ipv1, ipv2, ipv3) As nu) AS u FROM history WHERE active = '1' AND action = 'c' AND extra = '{$row['username']}'"));
								
								if(isset($rows['c']) && $rows['c'] > 0)
								{
									if($rows['u'] <= 0) $rows['u'] = 1;
									$extra = $rows['c'].' login attempt'.($rows['c'] == 1 ? ' was' : 's were').' made on your account made by '.$rows['u'].' distinct client'.($rows['u'] == 1 ? '' : 's');
									mysqli_query($dbc, "INSERT INTO history (action, ipv0, ipv1, ipv2, ipv3, entry_date, extra) VALUES ('f', $ipv0, $ipv1, $ipv2, $ipv3, '$r_timestamp', '$extra')");
								}
								
								//Update user's row with current SID and ECG_DATETIME
								mysqli_query($dbc, "UPDATE users SET SID = '".session_id()."' WHERE username = '$row[username]' LIMIT 1");
								mysqli_query($dbc, "UPDATE users SET connected = 'T' WHERE username = '$row[username]' LIMIT 1");
								mysqli_query($dbc, "UPDATE users SET ECG_DATETIME = '$r_timestamp' WHERE username = '$row[username]' LIMIT 1");
								
								//Since we've confirmed this guy as a legal user, remove (disable) any discrepancies he/she may have had with us in the past from the database!
								mysqli_query($dbc, "UPDATE history SET active = '0' WHERE action = 'c' AND active = '1' AND CONCAT(ipv0, '.', ipv1, '.', ipv2, '.', ipv3) = '$IP'");
								mysqli_query($dbc, "INSERT INTO history (action, ipv0, ipv1, ipv2, ipv3, entry_date, extra) VALUES ('b', $ipv0, $ipv1, $ipv2, $ipv3, '$r_timestamp', '$row[username]')");
								
								$_SESSION['u'] = $post['username'];
								$_SESSION['p'] = $post['password'];
								$_SESSION['username'] = $row['username'];
								$_SESSION['current_room'] = NULL;
								echo 'Approved';
							}
							
							else if($_POST['type'] == 'reg') echo 'Denied';
						}
						
						//Invalid username/password
						else
						{
							if($r)
							{
								if(mysqli_num_rows($result) != 0)
								{
									echo 'NotZeroError';
									mysqli_query($dbc, "INSERT INTO history (action, ipv0, ipv1, ipv2, ipv3, entry_date, extra) VALUES ('z', $ipv0, $ipv1, $ipv2, $ipv3, '$r_timestamp', '$post[username] / $post[password]')");
								}
								
								else
								{
									//A new user has successfully registered. Yay!
									mysqli_query($dbc, "INSERT INTO users (username, password, genesis, last_act_dt) VALUES ('$post[username]', '$post[password]', '$r_timestamp', '$r_timestamp')");
									mysqli_query($dbc, "INSERT INTO history (action, ipv0, ipv1, ipv2, ipv3, entry_date) VALUES ('g', $ipv0, $ipv1, $ipv2, $ipv3, '$r_timestamp')");
									echo 'Registered';
								}
							}
							
							else
							{
								$row = mysqli_fetch_array(mysqli_query($dbc, 'SELECT username FROM `users` WHERE SHA1(CONCAT(\''.substr($_SESSION['PYTHON']['challenge'], 0, 20).'\', username, \''.substr($_SESSION['PYTHON']['challenge'], 20, 20).'\')) = \''.$post['username'].'\' LIMIT 1'));
								if(!isset($row['username']) || empty($row['username'])) $row['username'] = '$NULL';
								mysqli_query($dbc, "INSERT INTO history (action, ipv0, ipv1, ipv2, ipv3, entry_date, extra) VALUES ('c', $ipv0, $ipv1, $ipv2, $ipv3, '$r_timestamp', '{$row['username']}')");
								echo 'Denied';
							}
						}
					}
				}
				
				//Close database connection
				mysqli_close($dbc);
			}
		}
		
		//Make sure we don't accidentally send any bad data!
		exit;
	}
	
	header("HTTP/1.0 404 Not Found");
	echo 'Hey, you\'re not a python program! Go away!'.($_SESSION['MAINTENANCE_MODE'] ? "\nBtw: The server is down for maintenance at the moment!" : '');
?>