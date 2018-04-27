%This script establishes a client connection to the rAIcer server to play
%the game.


%Connect to server
t=tcpclient('localhost',5007);

fprintf('Connection established, waiting for countdown... \n')

%wait for countdown
isCountdown=0;
while(isCountdown==0)
    stream=read(t,442374);
    if stream(2)==1
        isCountdown=1;
    end
end

fprintf('Countdown started, preprocessing...\n')


%TODO: Insert Preprocessing here, you have 10 seconds.


fprintf('Preprocessing done! Waiting for game to start...\n')

%wait for game start
isRunning=0;
ID=stream(1);
while(isRunning==0)
    stream=read(t,442374);
    if stream(2)==2
        isRunning=1;
    end
end

fprintf('Game started! Playing...\n')

%Playing the game
while(isRunning==1)

%receive image
stream=read(t,442374);
screen=stream(7:end);

%game finished?
if stream(2)==3
    fprintf('Game finished!\n')
    break
elseif stream(2)==4
    fprintf('Game over! You crashed!\n')
    break
elseif stream(2)==5
    fprintf('Game was stopped by server!\n')
    break
end

%show map:
%The next lines extract the image from the data stream.
J=uint8(screen);
Ir=reshape(J,[3,512,288]);
I=permute(Ir,[2,3,1]);
imagesc(I);

%TODO: Insert intelligence here

%TODO: Set the keys according to your decision system
keys=[0,0,0,0]; 

%send command
msg=uint8([ID,keys]);
write(t,msg);

end

fprintf('\n Game ended! \n')


