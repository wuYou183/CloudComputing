#include <iostream>
#include <string>
// #include <cmath>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include <mpi.h>
using namespace std;

const int N = 10000;
//粒子个数
int n = 256;
//频率
int timestep = 200;
//时间间隔 delta_time = 1/timestep
double delta_time;
//运行时长
int cycle_time = 100;

//数据存放
struct nobody{
	//重量
	double weight;
	//位置
	double px, py, pz;
	//速度
	double vx, vy, vz;
	//加速度
	double ax, ay, az;
};

//创建数据列表
nobody nobody_list[N];

//小球半径
double r = 0.01;
const double G = 1;

//生成数据
void make_data();
//读入数据
void read_data();
//写入数据
void write_data();
//计算力
void calcu_F(int);
//计算速度
void calcu_V(int);
//计算位置变化
void calcu_P(int);

void proc(int l){
	srand((unsigned)time(NULL));
	string s = std::to_string(l);
	string path = "data";
	path.append(s);
	path.append(".txt");
	freopen(path.c_str(), "w", stdout);
	for (int i = 0; i < n; ++i){
		//质量
		cout << nobody_list[i].weight << ' ';
		//x
		cout << nobody_list[i].px << ' ';
		//y
		cout << nobody_list[i].py << ' ';
		//z
		cout << nobody_list[i].pz << endl;
	}
	fclose(stdout);
}

int main(int argc, char *argv[]){
	make_data();
	read_data();
	delta_time = 1.0 / timestep;
	int myid, numprocs;
	clock_t starttime, endtime;

	MPI_Init(&argc, &argv);
	MPI_Comm_size(MPI_COMM_WORLD, &numprocs);
	MPI_Comm_rank(MPI_COMM_WORLD, &myid);
	double *mpi_buffer = (double *)malloc(sizeof(double) * 1000000);
	MPI_Buffer_attach(mpi_buffer, sizeof(double) * 1000000);

	starttime = clock();
	for (int i = 0; i < cycle_time; i++){
		for (int j = 0; j < numprocs; j++){
			if (j != myid){
				MPI_Bsend((nobody_list + (n / numprocs) * myid), sizeof(nobody) * n / numprocs, MPI_BYTE, j, i * 10 + myid, MPI_COMM_WORLD);
			}
		}

		for (int j = 0; j < numprocs; j++){
			if (j != myid){
				MPI_Status status;
				MPI_Recv((nobody_list + (n / numprocs) * j), sizeof(nobody) * n / numprocs, MPI_BYTE, j, i * 10 + j, MPI_COMM_WORLD, &status);
			}
		}

		for (int j = ( n / numprocs) * myid; j < ( n / numprocs) * (myid + 1); j++){
			calcu_F(j);
		}

		MPI_Barrier(MPI_COMM_WORLD);
		for (int j = ( n / numprocs) * myid; j < ( n / numprocs) * (myid + 1); j++){
			calcu_V(j);
			calcu_P(j);
		}
		MPI_Barrier(MPI_COMM_WORLD);
		//输出中间过程
		proc(i);
	}

	endtime = clock();
	cerr << "r=" << myid << endl;
	cerr << "t=" << (double)(endtime - starttime) / CLOCKS_PER_SEC << endl;

	if (myid != 0){
		MPI_Send((nobody_list + (n / numprocs) * myid), sizeof(nobody) * n / numprocs, MPI_BYTE, 0, myid, MPI_COMM_WORLD);
	}

	if (myid == 0){
		for (int i = 1; i < numprocs; i++){
			MPI_Status status;
			MPI_Recv((nobody_list + ( n / numprocs) * i), sizeof(nobody) * n / numprocs, MPI_BYTE, i, i, MPI_COMM_WORLD, &status);
		}
		write_data();
	}
	MPI_Finalize();
	return 0;
}

void make_data(){
	//随机种子
	srand((unsigned)time(NULL));
	freopen("data_in.txt", "w", stdout);

	for (int i = 0; i < 1 * n; ++i){
		//质量
		cout << (double)(rand() % 50 + 100) << ' ';
		//x
		cout << (double)(rand() % 50) << ' ';
		//y
		cout << (double)(rand() % 50) << ' ';
		//z
		cout << (double)(rand() % 50) << endl;
	}
	fclose(stdout);
}

void read_data(){
	freopen("data_in.txt", "r", stdin);

	for (int i = 0; i < n; ++i){
		//质量
		cin >> nobody_list[i].weight;
		//x
		cin >> nobody_list[i].px;
		//y
		cin >> nobody_list[i].py;
		//z
		cin >> nobody_list[i].pz;

		//初始化
		nobody_list[i].vx = 0;
		nobody_list[i].vy = 0;
		nobody_list[i].vz = 0;

		nobody_list[i].ax = 0;
		nobody_list[i].ay = 0;
		nobody_list[i].az = 0;
	}
	fclose(stdin);
}

void write_data(){
	freopen("data_out.txt", "w", stdout);

	for (int i = 0; i < n; ++i){
		//质量
		cout << nobody_list[i].weight << ' ';
		//x
		cout << nobody_list[i].px << ' ';
		//y
		cout << nobody_list[i].py << ' ';
		//z
		cout << nobody_list[i].pz << endl;
	}
	fclose(stdout);
}

void calcu_F(int index){ //计算作用力
	//初始化
	nobody_list[index].ax = 0;
	nobody_list[index].ay = 0;
	nobody_list[index].az = 0;

	//遍历测试
	for (int i = 0; i < n; ++i){
		if (i == index){
			continue;
		}
		//计算相对距离
		double dx, dy, dz;
		dx = nobody_list[index].px - nobody_list[i].px;
		dy = nobody_list[index].py - nobody_list[i].py;
		dz = nobody_list[index].pz - nobody_list[i].pz;

		double D = (dx * dx + dy * dy + dz * dz);

		//小于半径直接忽略，不考虑相撞
		if (D < r * r){
			D = r * r;
		}

		D *= sqrt(D);

		nobody_list[index].ax += G * nobody_list[i].weight * dx / D;
		nobody_list[index].ay += G * nobody_list[i].weight * dy / D;
		nobody_list[index].az += G * nobody_list[i].weight * dz / D;
	}
}

void calcu_V(int index){ //计算速度
	//加速度*时间叠加
	nobody_list[index].vx += nobody_list[index].ax * delta_time;
	nobody_list[index].vy += nobody_list[index].ay * delta_time;
	nobody_list[index].vz += nobody_list[index].az * delta_time;
}

void calcu_P(int index){ //计算位置
	//速度*时间+边界判断
	nobody_list[index].px += nobody_list[index].vx * delta_time;
	nobody_list[index].py += nobody_list[index].vy * delta_time;
	nobody_list[index].pz += nobody_list[index].vz * delta_time;
}