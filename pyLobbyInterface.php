<?php
	function mysqli_fetch_all($result)
	{
		//F**king Godaddy
		$fetch_all = array();
		while($all = mysqli_fetch_assoc($result)) $fetch_all[] = $all;
		return $fetch_all;
	}
	
	//Hello, python!
	if(isset($_POST['python'], $_POST['identity'], $_POST['method'], $_POST['u'], $_POST['p'], $_POST['SID']) && $_POST['python'] == 1)
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
		
		session_id(filter_var($_POST['SID'], FILTER_SANITIZE_STRING));
		session_start();
				
		//Maintenance mode (server offline when true)
		if($_SESSION['MAINTENANCE_MODE'])
		{
			echo 'MAINTENANCE_MODE';
			return;
		}
		
		if($_POST['u'] == $_SESSION['u'] && $_POST['p'] == $_SESSION['p'])
		{
			$dbc = mysqli_connect('mhousepython.db.4619325.hostedresource.com', '[REMOVED]', '[REMOVED]', '[REMOVED]');
			$post['identity'] = mysqli_real_escape_string($dbc, filter_var($_POST['identity'], FILTER_SANITIZE_STRING));

			//If they're sending a room connect request
			if($_POST['method'] == 'CONNECT' && isset($_POST['type']) && ($_POST['type'] == 'L' || $_POST['type'] == 'B'))
			{
				$result = mysqli_query($dbc, "SELECT room_id FROM server WHERE room_name = '$post[identity]' AND room_type = '$_POST[type]' LIMIT 1");
				
				if(mysqli_num_rows($result) == 1)
				{
					$row = mysqli_fetch_array($result);
					
					//if($row['max_users'] <= 0)
					//{
						$_SESSION['current_room'] = (int) $row['room_id'];
						echo 'Okay';
					//}
					
					/*else
					{
						//TODO - add back the "current_room" entry into the user portion of the MYSQL table
						$row2 = mysqli_fetch_array(mysqli_query($dbc, "SELECT COUNT(*) c FROM users WHERE current_room = '$row[room_id]' LIMIT 1"));
						
						if($row2['c'] < $row['max_users'])
							$_SESSION['current_room'] = int($row['room_id']);
							echo 'Okay';
						else echo 'Full';
					}*/
				}
				
				else echo 'NotFound';
			}
			
			//If they're asking for all the messages from a specific lobby starting from a specific timestamp
			//Requires method = GET and identity = timestamp-of-last-get
			else if($_POST['method'] == 'GET')
			{
				//Look for and report any public or private messages
				$data1 = array('private'=>array());
				$data2 = array('public'=>array());
				
				//Private
				$result = mysqli_query($dbc, "SELECT m.sender, m.body, u.status FROM messages m JOIN users u ON (u.username = m.sender) WHERE m.receiver = '$_SESSION[username]'");
				if(mysqli_num_rows($result))
				{
					$data1['private'] = mysqli_fetch_all($result);
					mysqli_query($dbc, "DELETE FROM messages WHERE receiver = '$_SESSION[username]'");
				}
				
				//Public
				if(isset($_SESSION['current_room']))
				{
					$result = mysqli_query($dbc, "SELECT m.sender, m.body, u.status FROM messages m JOIN users u ON (u.username = m.sender) WHERE m.room_id = $_SESSION[current_room] AND m.post_time >= '$post[identity]'");
					if(mysqli_num_rows($result)) $data2['public'] = mysqli_fetch_all($result);
				}
				
				echo json_encode(array_merge($data1, $data2));
			}
			
			//If they're attempting to "say" a message to the current lobby
			//These two both require method = SAY/WHISPER, identity = timestamp-of-send, and body = text body (sanatized by PHP)
			else if(isset($_POST['body'], $_SESSION['current_room']))
			{
				$post['body'] = mysqli_real_escape_string($dbc, filter_var($_POST['body'], FILTER_SANITIZE_STRING));
				if($_POST['method'] == 'SAY')
				{
					mysqli_query($dbc, "INSERT INTO messages (room_id, sender, body, post_time) VALUES ($_SESSION[current_room], '$_SESSION[username]', '$post[body]', '$post[identity]')");
					echo 'Okay';
				}
				
				//If they're attempting to "whisper" a message to some person
				//Requires target = valid_username
				else if($_POST['method'] == 'WHISPER' && isset($_POST['target']))
				{
					$post['target'] = mysqli_real_escape_string($dbc, filter_var($_POST['target'], FILTER_SANITIZE_STRING));
					$row = mysqli_fetch_array(mysqli_query($dbc, "SELECT COUNT(username) c FROM users WHERE username = '$_SESSION[target]' AND connected = 'T' LIMIT 1"));
					
					if($row['c'] == 1)
					{
						mysqli_query($dbc, "INSERT INTO messages VALUES (NULL, $_SESSION[current_room], '$_SESSION[username]', '$post[target]', '$post[body]', '$post[identity]')");
						echo 'Okay';
					}
						
					else echo 'Denied';
				}
				
				else die('EndOfLegalScriptIII');
			}
			
			else echo 'EndOfLegalScriptII';
			mysqli_close($dbc);
			exit;
		}
		
		else die('BadCreds');
		
		die('EndOfLegalScriptI');
	}
	//header('Location: http://dignityice.com/dg/Xunnamius/house/pyLoginInterface.php');
?>