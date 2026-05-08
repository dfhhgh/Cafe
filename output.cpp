#include <iostream>
#include <string>

using namespace std;

double add(double a, double b);

double add(double a, double b) {
    return (a + b);
}

int main() {
    cout << add(2, 3) << endl;
    return 0;
}
