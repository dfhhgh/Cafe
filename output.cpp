#include <iostream>
#include <string>

using namespace std;

double brew(double shots);

double brew(double shots) {
    if ((shots < 2)) {
        return 1;
    }
    return (shots * brew((shots - 1)));
}

int main() {
    double prices[3] = { 10, 20, 30 };
    bool ready = true;
    char cup = 'c';
    cout << cup << endl;
    cout << prices[1] << endl;
    cout << brew(5) << endl;
    return 0;
}
