#include<stdio.h>
#include<unistd.h>
#include<stdlib.h>

int main()
{
    char command[100];
    int pid;

    printf("Enter command: ");
    scanf("%s",command);

    pid=fork();

    if(pid<0)
    {
        printf("Fork failed\n");
        return 1;
    }

    if(pid==0)
    {
        printf("Child pid: %d\n",getpid());
        printf("Parent pid: %d\n",getppid());
        execlp(command,command,NULL);
    }
    else
    {
        printf("Current pid: %d\n",getpid());
        printf("Parent pid: %d\n",getppid());
    }

    return 0;
}