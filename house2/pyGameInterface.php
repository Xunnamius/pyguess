<?php
	function mysqlii_fetch_all($result)
	{
		$data = array();
		while($row = mysqli_fetch_assoc($result)) $data[] = $row;
		return $data;
	}
	
	function new_event($requestData, $responseData, $status='')
	{
		$eventLog = fopen('eventLog.txt', 'a');
		if(!empty($status)) $status = '-'.strtoupper($status).'-';
		fwrite($eventLog, "\n".$status.'['.gmdate('Y-m-d H:i:s', time()).'] '.(isset($_SESSION['userdata']['username'])? $_SESSION['userdata']['username'] : 'Unknown').' ('.$_SERVER['REMOTE_ADDR']."): $requestData   ->   $responseData");
		fclose($eventLog);
	}
	
	define('MAINTENANCE_MODE', false);
	
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
			new_event(http_build_query($_REQUEST), '(None)', 'BAD REQUEST');
			exit;
		}
		
		else $IP = $_SERVER['REMOTE_ADDR'];
		
		if(isset($_POST['SID'])) session_id(filter_var($_POST['SID'], FILTER_SANITIZE_STRING));
		session_start();
		
		//Maintenance mode (server offline when true)
		$_SESSION['MAINTENANCE_MODE'] = MAINTENANCE_MODE;
		if($_SESSION['MAINTENANCE_MODE'])
		{
			echo 'MAINTENANCE_MODE';
			return;
		}
		
		//If they're asking us for a random encryption code...
		if(isset($_POST['nec']) && $_POST['nec'] == 1)
		{
			$_SESSION['challenge'] = sha1(time().date('dmy')).rand(1, 10000);
			new_event(http_build_query($_POST), $_SESSION['challenge'].'@'.session_id());
			echo $_SESSION['challenge'].'@'.session_id();
		}
		
		//If they're trying to log in (or just requesting some user data)...
		else if(!empty($_POST['SID']))
		{
			if(!empty($_POST['u']) && !empty($_POST['p']))
			{
				//Connect to the MySQL server
				$dbc = mysqli_connect('mhousepython2.db.4619325.hostedresource.com', '[REMOVED]', '[REMOVED]', '[REMOVED]');
				$now = gmdate("Y-m-d H:i:s", time());
					
				//Escape the username and password
				$post['username'] = mysqli_real_escape_string($dbc, preg_replace("/[^0-9_a-zA-Z]/i", '', $_POST['u']));
				$post['password'] = mysqli_real_escape_string($dbc, $_POST['p']);
				
				//Automatically fail if the password doesn't match the escaped password
				if($_POST['p'] != $post['password'] || $_POST['u'] != $post['username'] || strlen($post['username']) > 40 || strlen($post['password']) > 40 || strlen($post['username']) < 4)
					echo 'Malformed';
				
				else if(isset($_POST['type']))
				{
					if($_POST['type'] == 'reg' && isset($_POST['class']))
					{
						$result = mysqli_query($dbc, 'SELECT username FROM users WHERE username = \''.$post['username'].'\'') or die('Denied1');
						
						//If the username(+password) matched
						if(mysqli_num_rows($result) == 0)
						{
							$post['class'] = mysqli_real_escape_string($dbc, (string)((int)($_POST['class'])));
							if(is_numeric($post['class']))
							{
								mysqli_query($dbc, "INSERT INTO users (username, password, class_id, free_sp) VALUES ('$post[username]', '$post[password]', $post[class], 50)") or die('Denied2');
								
								//Automatically assign class powers here
								if($post['class'] != 4)
									for($i=1; $i<=4; ++$i) mysqli_query($dbc, "INSERT INTO user_specials (username, special_id) VALUES ('$post[username]', ".($i + ($post['class']) * 4).')') or die('Denied3');
								else
									for($i=1; $i<=22; ++$i) mysqli_query($dbc, "INSERT INTO user_specials (username, special_id) VALUES ('$post[username]', $i)") or die('Denied4');
									
								new_event(http_build_query($_POST), 'Approved (for registration)');
								
								echo 'Approved';
								exit;
							}
						}
						
						new_event(http_build_query($_POST), 'Denied (for registration)');
						echo 'Denied';
					}
					
					else if($_POST['type'] == 'lin' && !isset($_SESSION['u'], $_SESSION['p']))
					{
						//Check the supplied credentials against our database (the meat and potatoes!)
						$result = mysqli_query($dbc, 'SELECT * FROM users WHERE SHA1(CONCAT(\''.substr($_SESSION['challenge'], 0, 20).'\', username, \''.substr($_SESSION['challenge'], 20, 20).'\')) = \''.$post['username'].'\' AND SHA1(CONCAT(\''.substr($_SESSION['challenge'], 0, 20).'\', password, \''.substr($_SESSION['challenge'], 20, 20).'\')) = \''.$post['password'].'\' LIMIT 1') or die('Denied1');
						
						//If the username(+password) matched
						if(mysqli_num_rows($result) == 1)
						{
							$_SESSION['u'] = $post['username'];
							$_SESSION['p'] = $post['password'];
							$_SESSION['userdata'] = mysqli_fetch_array($result);
							$_SESSION['current_room'] = NULL;
							new_event(http_build_query($_POST), 'Approved (for login)');
							echo 'Approved';
						}
						
						else
						{
							new_event(http_build_query($_POST), 'Denied (for login)');
							echo 'Denied';
						}
					}
					
					else if(isset($_SESSION['u'], $_SESSION['p']) && $post['username'] == $_SESSION['u'] && $post['password'] == $_SESSION['p'])
					{
						//If they're pulling user data...
						if($_POST['type'] == 'pul')
						{
							$row1 = mysqli_fetch_assoc(mysqli_query($dbc, 'SELECT * FROM users WHERE username = \''.$_SESSION['userdata']['username'].'\' LIMIT 1'));
							$row2 = mysqlii_fetch_all(mysqli_query($dbc, 'SELECT s.special_name AS name, s.special_desc AS `desc`, s.special_json AS json, u.allotted_sp AS sp FROM user_specials u NATURAL JOIN specials s WHERE u.username = \''.$_SESSION['userdata']['username'].'\''));
							
							$_SESSION['userdata'] = $row1;
							new_event(http_build_query($_POST), json_encode(array('userdata' => $row1, 'powers' => $row2)));
							echo json_encode(array('userdata' => $row1, 'powers' => $row2));
						}
						
						//If they're pushing a user data update...
						else if($_POST['type'] == 'psh' && isset($_POST['data']))
						{
							$post['data'] = explode(',', $_POST['data']);
							$tmpuserlvl1 = mysqli_fetch_array(mysqli_query($dbc, "SELECT level FROM users WHERE username = '".$_SESSION['userdata']['username']."' LIMIT 1"));
							mysqli_query($dbc, "UPDATE users SET wins = wins + ".$post['data'][2].", losses = losses + ".$post['data'][1].", free_sp = free_sp + ".$post['data'][0].", level = FLOOR(1 + FLOOR((wins / 2) + (losses / 4))) WHERE username = '".$_SESSION['userdata']['username']."' LIMIT 1") or die('SyntaxError2');
							$tmpuserlvl2 = mysqli_fetch_array(mysqli_query($dbc, "SELECT level FROM users WHERE username = '".$_SESSION['userdata']['username']."' LIMIT 1"));
							
							if($tmpuserlvl1['level'] != $tmpuserlvl2['level'])
							{
								echo 'Leveled:'.$tmpuserlvl2['level'];
								new_event(http_build_query($_POST), 'Leveled:'.$tmpuserlvl2['level']);
							}
							
							else
							{
								new_event(http_build_query($_POST), 'Updated (updates pushed into database)');
								echo 'Updated';
							}
						}
						
						//If they're pushing a user special powers update...
						else if($_POST['type'] == 'spp' && isset($_POST['target'], $_POST['modifier']))
						{
							$post['target'] = mysqli_fetch_array(mysqli_query($dbc, 'SELECT special_id FROM specials WHERE special_name = \''.mysqli_escape_string($dbc, $_POST['target']).'\' LIMIT 1'));
							$post['target'] = (int) $post['target']['special_id'];
							$post['modifier'] = (int) mysqli_escape_string($dbc, $_POST['modifier']);
							$free_sp = mysqli_fetch_array(mysqli_query($dbc, 'SELECT free_sp FROM users WHERE username = \''.$_SESSION['userdata']['username'].'\' LIMIT 1'));
							$free_sp = (int) $free_sp['free_sp'];
							
							if($post['modifier'] <= $free_sp)
							{
								mysqli_query($dbc, "UPDATE user_specials SET allotted_sp = allotted_sp + $post[modifier] WHERE username = '".$_SESSION['userdata']['username']."' AND special_id = {$post['target']} LIMIT 1") or die('SyntaxError1');
								mysqli_query($dbc, 'UPDATE users SET free_sp = '.($free_sp-$post['modifier'])." WHERE username = '".$_SESSION['userdata']['username']."' LIMIT 1") or die('SyntaxError2');
								
								new_event(http_build_query($_POST), 'Special Points were Pushed: remaining SP => '.($free_sp-$post['modifier']).'; special/mod => '.$post['target'].'/'.$post['modifier']);
								echo 'Valid';
							}
							
							else
							{
								echo 'Invalid';
								new_event(http_build_query($_POST), 'Special Points failed to get Pushed! (fsp: '.$free_sp.', mod: '.$post['modifier'].', tar: '.$post['target'].')');
							}
						}
						
						//If they're asking to log out
						else if($_POST['type'] == 'out')
						{
							$_SESSION = array();
							unset($_SESSION);
							
							//Stomp some bugs...
							session_regenerate_id();
							session_destroy();
							new_event(http_build_query($_POST), 'Goodbye (logged out)');
							echo 'Goodbye';
						}
						
						//If they're attempting to update a room
						else if($_POST['type'] == 'upd' && isset($_SESSION['current_room'], $_POST['data']))
						{
							$result = mysqli_query($dbc, "SELECT game_data FROM rooms WHERE room_id = $_SESSION[current_room] AND user1 IS NOT NULL AND user2 IS NOT NULL");
							if(mysqli_num_rows($result) == 0)
							{
								new_event(http_build_query($_POST), '$Die');
								die('$Die');
							}
							
							$allow = false;
							
							if($_POST['data'] == '$ClearGameData') $allow = 2;
							else
							{
								$result = mysqli_query($dbc, "SELECT game_data cmd FROM rooms WHERE room_id = $_SESSION[current_room] AND game_data != '' LIMIT 1") or die('$LookupError');
								$row = mysqli_fetch_assoc($result);
							
								if(mysqli_num_rows($result) == 1 && ($pos = stripos($row['cmd'], '$')) !== FALSE)
								{
									//This is a command!
									$cmd = substr(trim($row['cmd']), $pos+1, 3);
									new_event('SQL Result: '.http_build_query($row).'  <|>  $_POST: '.http_build_query($_POST), 'Command: '.$row['cmd'].' ['.$cmd.'] (pos '.stripos($row['cmd'], '$').') ', 'CMD');
									if($cmd == 'Die' or $cmd == 'Win' or $cmd == 'Ski')
									{
										new_event(http_build_query($_POST), $row['cmd']);
										echo $row['cmd'];
									}
									
									else if($cmd == 'Yes' && substr($_POST['data'], 0, 6) == '$Skip:' or substr($_POST['data'], 0, 4) == '$Die' or substr($_POST['data'], 0, 4) == '$Win')
									{
										new_event(http_build_query($_POST), '$allow = true (1)');
										$allow = true;
									}
									
									else if($cmd == 'Ali' && substr($_POST['data'], 0, 7) == '$Alive:')
									{
										new_event(http_build_query($_POST), '$Die (cmd)');
										echo '$Die';
									}
									
									else
									{
										new_event(http_build_query($_POST), $row['cmd']);
										echo $row['cmd'];
									}
								}
								
								else if(mysqli_num_rows($result) == 0)
								{
									new_event(http_build_query($_POST), '$allow = true (2)');
									$allow = true;
								}
								
								else if(mysqli_num_rows($result) == 1)
								{
									new_event(http_build_query($_POST), $row['cmd']);
									echo $row['cmd'];
								}
							}
							
							if($allow)
							{
								mysqli_query($dbc, "UPDATE rooms SET game_data = '".($allow === 2 ? '' : $_POST['data'])."', last_activity_dt = '$now' WHERE room_id = $_SESSION[current_room] LIMIT 1") or die('$UpdateFailed');
								new_event("SQL Query: UPDATE rooms SET game_data = '".($allow === 2 ? '' : $_POST['data'])."', last_activity_dt = '$now' WHERE room_id = $_SESSION[current_room] LIMIT 1", '$Updated (allowed)');
								echo '$Updated';
							}
						}
						
						//If they're attempting to kill their current room
						else if($_POST['type'] == 'kil' && isset($_SESSION['current_room']))
						{
							mysqli_query($dbc, "UPDATE rooms SET user1 = NULL WHERE room_id = $_SESSION[current_room] AND user1 = '".$_SESSION['userdata']['username']."' LIMIT 1") or die('DeathError1');
							mysqli_query($dbc, "UPDATE rooms SET user2 = NULL WHERE room_id = $_SESSION[current_room] AND user2 = '".$_SESSION['userdata']['username']."' LIMIT 1") or die('DeathError2');
							$_SESSION['current_room'] = NULL;
							new_event(http_build_query($_POST), 'Murdered '.$_SESSION['userdata']['username'], 'KILL_CMD');
							echo 'Murdered';
						}
						
						//If they're challenging another user
						else if($_POST['type'] == 'cha' && isset($_POST['chal']))
						{
							$post['chal'] = mysqli_real_escape_string($dbc, $_POST['chal']);
							
							if($post['chal'] == $_SESSION['userdata']['username']) echo '$Illegal';
							else
							{
								$result = mysqli_query($dbc, "SELECT room_id FROM rooms WHERE BINARY user1 = '".$_SESSION['userdata']['username']."' LIMIT 1");
								if(mysqli_num_rows($result) == 0)
								{
									$result = mysqli_query($dbc, "SELECT room_id FROM rooms WHERE BINARY user1 = '$post[chal]' AND user2 = '".$_SESSION['userdata']['username']."' AND game_data = 'Waiting for ".$_SESSION['userdata']['username']."...' LIMIT 1");
									
									//If the challenge is a response to another user's challenge (check for this), prepare for battle!
									if(mysqli_num_rows($result) == 1)
									{
										$row = mysqli_fetch_array($result);
										$_SESSION['current_room'] = $row['room_id'];
										
										//May combine next two lines into one using subqueries later
										$randUser = mysqli_fetch_array(mysqli_query($dbc, 'SELECT user'.(rand(1, 2)).' AS u FROM rooms WHERE room_id = '.$row['room_id'].' LIMIT 1'));
										mysqli_query($dbc, "UPDATE rooms SET game_data = 'Starting game, first is $randUser[u]' WHERE room_id = $_SESSION[current_room] LIMIT 1");
										
										echo '$ChallengedWaiting';
									}
									
									//Create a new battle room (if challengee isn't busy)!
									else
									{
										$result = mysqli_query($dbc, 'SELECT username FROM users WHERE BINARY username = \''.$post['chal'].'\' LIMIT 1');
										
										//User exists
										if($post['chal'] == $_POST['chal'] && mysqli_num_rows($result) == 1)
										{
											//Check if the user is busy or not
											$result = mysqli_query($dbc, "SELECT room_id FROM rooms WHERE user1 = '$post[chal]' OR user2 = '$post[chal]' LIMIT 1");
											
											//User is not busy, challenge them!
											if(mysqli_num_rows($result) == 0)
											{
												//Create room, set $_SESSION['current_room'], etc.
												mysqli_query($dbc, "INSERT INTO rooms VALUES ('', '$now', 'Waiting for $post[chal]...', '".$_SESSION['userdata']['username']."', '$post[chal]', NULL)");
												$row = mysqli_fetch_array(mysqli_query($dbc, "SELECT room_id FROM rooms WHERE user1 = '".$_SESSION['userdata']['username']."' AND user2 = '$post[chal]' LIMIT 1"));
												
												$_SESSION['current_room'] = $row['room_id'];
												echo '$ChallengerWaiting';
											}
											
											//User is busy, too bad!
											else echo '$Busy';
										}
										
										//User doesn't exist!
										else echo '$NoMatch';
									}
								}
								
								else echo '$AlreadyWaiting';
							}
						}
						
						//If they're requesting pending room battle data
						else if($_POST['type'] == 'bat')
						{
							if(isset($_SESSION['current_room'])) echo '$Ingame';
							else
							{
								$result = mysqli_query($dbc, "SELECT user1, room_id FROM rooms WHERE game_data = 'Waiting for ".$_SESSION['userdata']['username']."...' AND user2 = '".$_SESSION['userdata']['username']."' AND switch IS NULL LIMIT 1");
								
								if(mysqli_num_rows($result) == 1)
								{
									$row = mysqli_fetch_array($result);
									mysqli_query($dbc, "UPDATE rooms SET switch = 'T', last_activity_dt = '$now' WHERE room_id = $row[room_id] LIMIT 1");
									echo $row['user1'];
									exit;
								}
								
								echo '$NoBattle';
							}
						}
						
						else if($_POST['type'] == 'bat2' && isset($_SESSION['current_room']))
						{
							$result = mysqli_query($dbc, "SELECT game_data, user2 FROM rooms WHERE room_id = $_SESSION[current_room] LIMIT 1");
							
							if(mysqli_num_rows($result) == 1)
							{
								$row = mysqli_fetch_array($result);
								if(strpos($row['game_data'], 'Starting game, first is ') !== FALSE)
								{
									$first = substr($row['game_data'], 24);
									mysqli_query($dbc, "UPDATE rooms SET game_data = 'Acknowledged: $first', last_activity_dt = '$now' WHERE room_id = $_SESSION[current_room] LIMIT 1");
									echo json_encode(array('opponent' => $row['user2'], 'first' => $first));
									exit;
								}
							}
							
							echo '$NoDice';
							mysqli_query($dbc, "UPDATE rooms SET last_activity_dt = '$now' WHERE room_id = $_SESSION[current_room] LIMIT 1");
						}
						
						else if($_POST['type'] == 'bat3' && isset($_SESSION['current_room']))
						{
							$result = mysqli_query($dbc, "SELECT game_data, user1 FROM rooms WHERE room_id = $_SESSION[current_room] AND user1 IS NOT NULL AND user2 IS NOT NULL LIMIT 1");
							
							if(mysqli_num_rows($result) == 1)
							{
								$row = mysqli_fetch_array($result);
								if(strpos($row['game_data'], 'Acknowledged: ') !== FALSE) //Make this better. strpos should go into substr!
								{
									$first = substr($row['game_data'], 14);
									mysqli_query($dbc, "UPDATE rooms SET game_data = '', last_activity_dt = '$now' WHERE room_id = $_SESSION[current_room] LIMIT 1");
									echo json_encode(array('opponent' => $row['user1'], 'first' => $first));
									exit;
								}
							}
							
							echo '$NoDice';
							mysqli_query($dbc, "UPDATE rooms SET last_activity_dt = '$now' WHERE room_id = $_SESSION[current_room] LIMIT 1");
						}
						
						else if($_POST['type'] == 'bat4' && isset($_SESSION['current_room'], $_POST['opponent']))
						{
							if(isset($_POST['ignore'])) $_POST['ignore'] = mysqli_real_escape_string($dbc, $_POST['ignore']);
							$result = mysqli_query($dbc, "SELECT game_data FROM rooms WHERE room_id = $_SESSION[current_room] AND user1 IS NOT NULL AND user2 IS NOT NULL");
							if(mysqli_num_rows($result) == 0) die('$Die');
							
							$result = mysqli_query($dbc, "SELECT game_data FROM rooms WHERE room_id = $_SESSION[current_room] AND (SUBSTR(game_data,1,1) = '".'$'."' OR LOCATE('".$_SESSION['userdata']['username']."', game_data) = 0)".(isset($_POST['ignore']) ? " AND LOCATE('$_POST[ignore]', game_data) = 0" : '').' LIMIT 1') or die('$BadQuery');
							
							if(mysqli_num_rows($result) == 1)
							{
								$row = mysqli_fetch_assoc($result);
								mysqli_query($dbc, "UPDATE rooms SET game_data = '', last_activity_dt = '$now' WHERE room_id = $_SESSION[current_room] AND SUBSTR(game_data,1,1) != '".'$'."' LIMIT 1");
								echo $row['game_data'];
								exit;
							}
							
							echo '$NoData';
							mysqli_query($dbc, "UPDATE rooms SET last_activity_dt = '$now' WHERE room_id = $_SESSION[current_room] LIMIT 1");
						}
						
						//Sent to the server periodically to prove client liveliness
						else if($_POST['type'] == 'ali' && isset($_SESSION['current_room']))
						{
							$query = "SELECT game_data FROM rooms WHERE room_id = $_SESSION[current_room] AND game_data = '".'$Alive:'.$_SESSION['userdata']['username']."' LIMIT 1";
							
							if(mysqli_num_rows(mysqli_query($dbc, $query)) == 1)
							{
								$row = mysqli_fetch_assoc($result);
								mysqli_query($dbc, "UPDATE rooms SET game_data = '$Yes', last_activity_dt = '$now' WHERE room_id = $_SESSION[current_room] LIMIT 1");
								new_event(http_build_query($_POST), '(None)', 'ALIVE');
							}
							
							mysqli_query($dbc, "UPDATE rooms SET last_activity_dt = '$now' WHERE room_id = $_SESSION[current_room] LIMIT 1");
						}
						
						//If they're requesting data on another user
						else if($_POST['type'] == 'req' && isset($_POST['stat']))
						{
							$post['stat'] = mysqli_real_escape_string($dbc, $_POST['stat']);
							$result = mysqli_query($dbc, 'SELECT u.level le, u.wins w, u.losses lo, c.class_name n, room_id rid FROM users u NATURAL JOIN classes c LEFT OUTER JOIN rooms r ON (r.user1 = u.username OR r.user2 = u.username) WHERE BINARY u.username = \''.$post['stat'].'\' LIMIT 1');
						
							//If the username(+password) matched
							if(mysqli_num_rows($result) == 1)
							{
								$row = mysqli_fetch_array($result);
								echo $row['n'].' '.$post['stat'].' (level '.$row['le'].'): '.$row['w'].' wins/'.$row['lo'].' losses'."\n  ".'This user is currently '.(!isset($row['rid'])?'NOT ':'').'in a match.';
							}
							
							else echo 'BadUser';
						}
						
						else echo 'Unknown type '.$_POST['type'];
					}
					
					else echo 'Unknown command.';
				}
				
				//Close database connection & datafile stream
				mysqli_close($dbc);
			}
		}
		
		//Make sure we don't accidentally send any bad data!
		exit;
	}
	
	header("HTTP/1.0 404 Not Found"); //Really, people shouldn't be coming here...
	echo '<p>Game Server Status: <span style="color: '.(!MAINTENANCE_MODE ? 'green">Online' : 'red">Offline').'!</span></p>';
	echo '<p><a href="eventLog.txt" title="Server Event Log">Click here</a> to access the server\'s event log.</p>'; 
?>