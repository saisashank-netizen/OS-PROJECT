  GNU nano 8.7.1                                                practical2.c
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>

int main()
{
    int source, destination;
    char buf[50];
    int n;

    source = open("source.txt", O_RDONLY);
    destination = open("destination.txt", O_RDWR);

    n = read(source, buf, 50);
    write(destination, buf, n);

    close(source);
    close(destination);

    printf("File copied successfully\n");

    return 0;
}
