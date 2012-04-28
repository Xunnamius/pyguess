<?php
	//TODO - Take redundant code and put it into a global php file (chmoded), clean up the code, make it more prettyful (on ALL pages), etc.
	$run_interval = 20; //How many seconds to wait in between running the ECG code
	$total_run_time = 300; //Total time the script should run (10 minutes represented in seconds)
	
	//Although sleep doesn't count towards this limit, this is to make sure daemon crons don't spill over into each other for some odd reason
	ini_set('max_execution_time', $total_run_time);
	set_time_limit($total_run_time);
	
	$iterator = 0;
	$total_iterations = floor($total_run_time / $run_interval);
	
	if(empty($_SERVER['REMOTE_ADDR']) && empty($_SERVER['HTTP_USER_AGENT']))
	{
		$dbc = mysqli_connect('mhousepython.db.4619325.hostedresource.com', '[REMOVED]', '[REMOVED]', '[REMOVED]');
		$dbc2 = mysqli_connect('mhousepython.db.4619325.hostedresource.com', '[REMOVED]', '[REMVOED]', '[REMOVED]');
		
		for(; $iterator < $total_iterations; ++$iterator)
		{
			$now = gmdate("Y-m-d H:i:s", time());
			$time = time();
			$result = mysqli_query($dbc, "SELECT username FROM users WHERE connected = 'T' AND ECG_DATETIME + INTERVAL 10 SECOND < '".$now.'\'');
			while($row = mysqli_fetch_array($result)) mysqli_query($dbc, "UPDATE users SET connected = 'F' WHERE username = '$row[username]' LIMIT 1");
			mysqli_query($dbc, "DELETE FROM messages WHERE post_time + INTERVAL 60 SECOND < '".$now."'");
			mysqli_query($dbc2, "DELETE FROM rooms WHERE last_activity_dt + INTERVAL 30 SECOND < '".$now."'");
			@sleep($run_interval - (time() - $time));
		}
		
		mysqli_close($dbc);
		mysqli_close($dbc2);
		exit;
	}
	
	header('Location: http://dignityice.com/dg/Xunnamius/house/pyLoginInterface.php');
?>