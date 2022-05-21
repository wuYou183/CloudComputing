# 创建任务（pod）=> kubectl apply -f nb2.yaml
def create_pod():
    import yaml
    from kubernetes import client, config
    from openshift.dynamic import DynamicClient
    
    # 连接K8s，DynamicClient（MPIJob属于自创类型，进行无头创建）
    k8s_client = config.new_client_from_config()
    dyn_client = DynamicClient(k8s_client)
    v1_services = dyn_client.resources.get(api_version='kubeflow.org/v1', kind='MPIJob')  # 导入自创的MPIJob类型以及版本
    
    with open(os.path.join(os.path.join(os.getcwd()),'/home/k8suser/mpi-operator/examples/v2beta1/nbody2//nb2.yaml')) as f:  # 读取YAML文件
        service_data = yaml.safe_load(f)

    resp = v1_services.create(body=service_data, namespace='default')
    return resp.metadata

# 删除任务，每次创建前都需要删除 => kubectl delete -f nb2.yaml
def delete_pod():
    import yaml
    from kubernetes import client, config
    from openshift.dynamic import DynamicClient
    
    k8s_client = config.new_client_from_config()
    dyn_client = DynamicClient(k8s_client)
    v1_services = dyn_client.resources.get(api_version='kubeflow.org/v1', kind='MPIJob')
    
    v1_services.delete(name='nb2', namespace='default')

# 获取所有的pod信息（pod的IP、命名空间、pod的名字、所在节点的IP）=> kubectl get pods (-A) (-o wide)
def get_all_information():
    from kubernetes import client, config
    import numpy as np
    
    config.kube_config.load_kube_config(config_file="/root/jupyternotebook/kubeconfig.yaml")  # K8s认证
    v1 = client.CoreV1Api()  # 调用API接口
    ret = v1.list_pod_for_all_namespaces(watch=False)  
    
    a=list()
    b=list()
    c=list()
    d=list()
    
    for i in ret.items:
        a.append(i.status.pod_ip)
        b.append(i.metadata.namespace)
        c.append(i.metadata.name)
        d.append(i.status.host_ip)
    return a,b,c,d

# 获取命名空间 => kubectl get namespaces
def get_namespace():
    from kubernetes import client, config
    config.kube_config.load_kube_config(config_file="/root/jupyternotebook/kubeconfig.yaml")
    v1 = client.CoreV1Api()
    a=list()
    for ns in v1.list_namespace().items:
        a.append(ns.metadata.name)
    return a

# 获取pod的日志 => 1、 kubectl logs nb2-.... -n default (-f)  2、 kubectl describe pod nb2-... -n default
def get_pod_logs(str_name):
    from kubernetes import client, config
    config.kube_config.load_kube_config(config_file="/root/jupyternotebook/kubeconfig.yaml")
    v1 = client.CoreV1Api()
    log_content = v1.read_namespaced_pod_log('nb2-launcher-'+str_name, 'default', pretty=True, tail_lines=200)
    return log_content

# 修改YAML文件，修改并行数
import yaml,json,os,sys
class Change_yaml:
    def __init__(self,pod_num):
        self.job_name='nb2'
        self.file_path= '/home/k8suser/mpi-operator/examples/v2beta1/nbody2/nb2.yaml'
        self.namespace='default'
 
    def file_content(self):
        # 打开yaml文件读取
        file = open(self.file_path,"r",encoding='UTF-8')
        file_content = file.read()
        file.close()
        return file_content
 
    def file_write(self,dict_yaml):
        # 写入文件
        file = open(self.file_path,"w")
        file.write(dict_yaml)
        file.close()
 
    def yaml_dict(self,yaml_content):
        # 将读取到的Yaml文件转换为字典格式
        yaml_dict = yaml.load(yaml_content,Loader=yaml.FullLoader)
        return yaml_dict
 
    def change_dict_env(self,yaml_dict,pod_num):
        # 修改进程数
        yaml_dict['spec']['mpiReplicaSpecs']['Launcher']['template']['spec']['containers'][0]['args'][2]=pod_num
        yaml_dict['spec']['mpiReplicaSpecs']['Worker']['replicas']=int(pod_num)
        return yaml_dict
 
    def dict_yaml(self,yaml_dict):
        # 将dict转换为yaml文件
        new_yaml_str = yaml.dump(yaml_dict)
        return new_yaml_str
   
def patch_pod(pod_num):
    class_func=Change_yaml(pod_num)
    yaml_content = class_func.file_content()
    yaml_dict = class_func.yaml_dict(yaml_content)
    yaml_dict = class_func.change_dict_env(yaml_dict,pod_num)
    dict_yaml = class_func.dict_yaml(yaml_dict)
    class_func.file_write(dict_yaml)
    return yaml_dict

# 图形界面
from tkinter import *
import numpy as np
from matplotlib import pyplot as plt  # 用来绘制图形
from mpl_toolkits.mplot3d import Axes3D

root=Tk()
root.title("Cloud Computing")  #标题
root.geometry("600x400+500+200")  #窗口大小:长，宽，位置

#输入文本框
entry=Entry(root,width=30,bd=5,bg='#eee5de') 
entry.grid(row=1,column=2)

#输出文本框
text=Text(root,width=100,height=30)
text.grid(row=4,column=1,columnspan=3)

#按钮功能
def com_create():
    text.delete(1.0,'end')
    metadata=create_pod()
    text.insert(INSERT,metadata)
    
def com_delete():
    text.delete(1.0,'end')
    delete_pod()
    text.insert(INSERT,'The pods are deleted successfully!')

def com_get_pod_logs():
    text.delete(1.0,'end')
    str_name=entry.get()
    a=get_pod_logs(str_name)
    text.insert(INSERT,a)

def com_get_all_information():
    text.delete(1.0,'end')
    a,b,c,d=get_all_information()
    for i in range(len(a)):
        text.insert(INSERT,a[i])
        text.insert(INSERT,'\t')
        text.insert(INSERT,b[i])
        text.insert(INSERT,'\t')
        text.insert(INSERT,c[i])
        text.insert(INSERT,'\t')
        text.insert(INSERT,d[i])
        text.insert(INSERT,'\n')
    
def com_get_namespace():
    text.delete(1.0,'end')
    a=get_namespace()
    text.insert(INSERT,a)

def com_patch():
    text.delete(1.0,'end')
    pod_num=entry.get()
    yaml_dict=patch_pod(pod_num)
    text.insert(INSERT,yaml_dict)

def com_get_yaml():
    text.delete(1.0,'end')
    service_data=get_yaml()
    text.insert(INSERT,service_data)
    
#按钮
button1=Button(root,text="creat",command=com_create,width=30,height=2)
button1.place(x=300,y=50)
button1.grid(row=2,column=1)

button2=Button(root,text="delete",command=com_delete,width=30,height=2)
button2.place(x=300,y=50)
button2.grid(row=2,column=2)

button7=Button(root,text="get yaml",command=com_get_yaml,width=30,height=2)
button7.place(x=300,y=50)
button7.grid(row=2,column=3)

button3=Button(root,text="get pod logs",command=com_get_pod_logs,width=30,height=2)
button3.place(x=300,y=50)
button3.grid(row=3,column=1)

button4=Button(root,text="get all information",command=com_get_all_information,width=30,height=2)
button4.place(x=300,y=50)
button4.grid(row=3,column=2)

button5=Button(root,text="get namespace",command=com_get_namespace,width=30,height=2)
button5.place(x=300,y=50)
button5.grid(row=3,column=3)

button6=Button(root,text="patch",command=com_patch,width=30,height=2)
button6.place(x=300,y=50)
button6.grid(row=1,column=3)

#标签
label1=Label(root,text='input the pod_num/str_name')
label1.grid(row=1,column=1)
root.mainloop()

# 动态图
import matplotlib.pyplot as plt 
import matplotlib.animation as animation
import numpy as np
from matplotlib import pyplot as plt  # 用来绘制图形
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation

%matplotlib qt5  # jupyter notebook 弹窗

path='/data/'  # NFS => nfs节点 => 每次重启需要执行：systemctl start nfs => 其余节点需执行：mount -t nfs k8s-nfs:/opt/k8s /data/ => 解除命令：umount /data/

w=np.zeros(150)
x=np.zeros(150)
y=np.zeros(150)
z=np.zeros(150)

fig=plt.figure(figsize=(10,10))
ax1 = Axes3D(fig)

def gen_path(m):
    global w,x,y,z
    if m==0:
        pathi=path+'data_in.txt'
    elif m==100:
        pathi=path+'data_out.txt'
    else:
        pathi=path+'data'+str(m)+'.txt'
    with open(pathi) as f:
        s=0
        for line in f:
            if len(line)<4:
                continue
            if s<150:
                w[s]=(int(float(line.split()[0])))
                x[s]=(line.split()[1])
                y[s]=(line.split()[2])
                z[s]=(line.split()[3])
                s=s+1
    return w,x,y,z

def update(i):
    label = 'timestep {0}'.format(i)
    ax1.cla()
    m = 5 * i
    w,x,y,z = gen_path(m)
    ax1.set_xlabel(label)
    ax1.scatter3D(x[:], y[:], z[:], w[:], cmap='Greens')
    return ax1

anim = FuncAnimation(fig, update, frames=np.arange(0, 21), interval=1000)
plt.show()