'''
2018-09-17
载入149家新材料企业的经营数据
'''

import numpy as np

def load_data(filename):
    '''
    载入数据
    :param filename: 东方财富网上爬下来的企业数据'crawl_eastmoney.csv'
    :return: 经过处理后的数据特征名称列表和数据值列表
    '''
    fr=open(filename,'r')
    content=fr.readlines()
    all_names=content[0].strip().strip('\ufeff').split(',')
    all_datas=[i.strip().split(',') for i in content if '净利润' not in i]     #提取不含标题名称的数据内容

    x1,x2,x3=all_names.index('公司代码'),all_names.index('公司名称'),all_names.index('报告期')     #去掉不需要的标识数据
    ret_names=all_names[:x1]+all_names[x1+1:x2]+all_names[x2+1:x3]+all_names[x3+1:]
    ret_datas=[data[:x1]+data[x1+1:x2]+data[x2+1:x3]+data[x3+1:] for data in all_datas]

    x=ret_names.index('股票价格')       #只查询到最新的股票价格，以往报告期的股票价格用平均值代替
    y = dict();strs = []
    for datas in ret_datas:
        for data in datas:
            ind = datas.index(data)
            if '%' in data:
                datas[ind] = float(data[:-1])
            if ind == x and data == '0':
                datas[ind] = '--'
            try:
                datas[ind] = float(datas[ind])
            except:
                strs.append(datas[ind])
    # print(strs)
    # print(ret_datas)
    s = [x for x in strs if '%' not in x]
    for datas in ret_datas:
        for data in datas:
            ind = datas.index(data)
            if data in s:
                if ind not in y.keys():         # 缺失值也用平均值代替
                    others = [x[ind] for x in ret_datas if x[ind] not in s]
                    # print(others)
                    meaVal = np.mean(np.array(others).astype('float32'))
                    y[ind] = meaVal
                datas[ind] = y[ind]
    return ret_names,ret_datas


# def normalize(datamat):
#     m,n=np.shape(datamat)
#     maxMat=np.max(datamat,0)
#     minMat=np.min(datamat,0)
#     diffMat=maxMat-minMat
#     retData=np.zeros((m,n))
#     for i in range(n):
#         retData[:,i]=(datamat[:,i]-minMat[i])/diffMat[i]
#     return retData


def calc1_Zscore(names,datas):
    #指标体系1，Z计分法
    z_class=[];scos=[]
    for dat in datas:
        # if dat[names.index('总负债')] ==0:
        #     dat[names.index('总负债')]=float('inf')
        # if dat[names.index('总资产')]==0:
        #     dat[names.index('总资产')]=float('inf')
        x1=(dat[names.index('流动资产')]-dat[names.index('流动负债')])/dat[names.index('总资产')]
        x2=(dat[names.index('未分配利润')]+dat[names.index('盈余公积金')])/dat[names.index('总资产')]
        x3=dat[names.index('利润总额')]/dat[names.index('总资产')]
        x4=(dat[names.index('总股本')]*dat[names.index('股票价格')])/dat[names.index('总负债')]
        x5=dat[names.index('营业收入')]/dat[names.index('总资产')]
        score=1.2*x1+1.4*x2+3.3*x3+0.6*x4+0.999*x5
        scos.append(score)

        if score>3:
            c='健康'
        elif score>1.5:
            c='可疑'
        else:
            c='危险'
        z_class.append(c)
    return z_class,scos


def calc_indecis(values,mark='-',reverse=1):
    '''
    计算某特征数据相邻报告期的差值或平均值
    :param values: 某特征数据列表
    :param mark: 标识相加或相减
    :param reverse: 1标识为新报告期-旧报告期，，0标识旧报告期-新报告期
    :return: 某特征数据相邻报告期的差值或平均值
    '''
    calc_vals=[]
    for i in range(149):
        for j in range(5):
            if mark=='-':
                val=values[i+j]-values[i+j+1]
                if reverse==0:
                    val=-val
            else :
                val=(values[i+j+1]+values[i+j])/2
            calc_vals.append(val)
        calc_vals.append('')    #最旧报告期的差值或平均值标为缺失值，用总均值代替

    others = [x for x in calc_vals if x != '']
    meaVal = np.mean(others)
    for val in calc_vals:
        if val=='':
            calc_vals[calc_vals.index(val)]=meaVal
    return calc_vals


def calc2_bathory(names,datas):
    #指标体系2，巴萨利模型
    scos=[]
    sta=[x[names.index('固定资产')] for x in datas]
    diff_sta=calc_indecis(sta,'-',0)
    for dat in datas:
        A=(dat[names.index('利润总额')]+diff_sta[datas.index(dat)]+dat[names.index('递延所得税资产')])/dat[names.index('流动负债')]
        B=dat[names.index('利润总额')]/(dat[names.index('流动资产')]-dat[names.index('流动负债')])
        C=dat[names.index('股东权益')]/dat[names.index('流动负债')]
        D=(dat[names.index('总资产')]-dat[names.index('无形资产')]-dat[names.index('总负债')])/dat[names.index('总负债')]
        E=(dat[names.index('流动资产')]-dat[names.index('流动负债')])/dat[names.index('总资产')]
        sco=A+B+C+D+E
        scos.append(sco)
    return scos


def calc3_Fscore(names,datas):
    #指标体系3，F分数
    f_class=[];scos=[]
    sta = datas[:,names.index('固定资产')]
    diff_sta = calc_indecis(sta, '-', 0)
    deb = datas[:,names.index('总负债')]
    avg_deb = calc_indecis(deb, '+')
    ins = datas[:, names.index('总资产')]
    avg_ins = calc_indecis(ins, '+')

    for i in range(len(datas)):
        dat=datas[i]
        x1 = (dat[names.index('流动资产')] - dat[names.index('流动负债')]) / dat[names.index('总资产')]
        x2 = (dat[names.index('未分配利润')] - dat[names.index('盈余公积金')]) / dat[names.index('总资产')]
        x3=(dat[names.index('净利润')]+diff_sta[i])/avg_deb[i]
        x4 = (dat[names.index('总股本')] * dat[names.index('股票价格')]) / dat[names.index('总负债')]
        x5=(dat[names.index('净利润')]+dat[names.index('应付利息')]+diff_sta[i])/avg_ins[i]
        score=-0.1774+1.1091*x1+0.1074*x2+1.9271*x3+0.0302*x4+0.4961*x5
        scos.append(score)

        if score>0.1049:
            f_class.append('健康')
        elif score>-0.0501:
            f_class.append('可疑')
        else:
            f_class.append(('危险'))
    return f_class,scos



def pre_value(value):
    #得到前一个报告期的数据值
    pre_val=[]
    for i in range(149):
        for j in range(5):
            pre_val.append(value[i+j+1])
        pre_val.append('')
    others = [x for x in pre_val if x != '']
    meaVal = np.mean(others)
    for val in pre_val:
        if val == '':
            pre_val[pre_val.index(val)] = meaVal
    return pre_val


def calc4_wall(names,datas):
    #指标体系4，沃尔评分法
    acc=datas[:,names.index('应收账款')]
    avg_acc=np.array(calc_indecis(acc,'+'))
    sto = datas[:, names.index('存货')]
    avg_sto = np.array(calc_indecis(sto, '+'))
    sale = datas[:, names.index('营业收入')]
    dif_sale = np.array(calc_indecis(sale))
    pre_sale=np.array(pre_value(sale))
    pro = datas[:, names.index('净利润')]
    dif_pro= np.array(calc_indecis(pro))
    pre_pro=np.array(pre_value(pro))
    ins = datas[:, names.index('总资产')]
    dif_ins = np.array(calc_indecis(ins))
    pre_ins=np.array(pre_value(ins))

    net_pro=datas[:,names.index('净利润')]/datas[:,names.index('总资产')]
    net_sale=datas[:,names.index('净利润')]/datas[:,names.index('营业收入')]
    net_ret=datas[:,names.index('净利润')]/(datas[:,names.index('总资产')]-datas[:,names.index('总负债')])
    self_ins=(datas[:,names.index('总资产')]-datas[:,names.index('总负债')])/datas[:,names.index('总资产')]
    flow_rate=datas[:,names.index('流动资产')]/datas[:,names.index('流动负债')]
    acc_rec=datas[:,names.index('营业收入')]/avg_acc
    sto_rate=datas[:,names.index('销售费用')]/avg_sto
    sale_inc=dif_sale/pre_sale
    pro_inc=dif_pro/pre_pro
    ins_inc=dif_ins/pre_ins

    feas=np.array([net_pro,net_sale,net_ret,self_ins,flow_rate,acc_rec,sto_rate,sale_inc,pro_inc,ins_inc])

    max_feas=feas.max(1)
    weights=np.array([0.2,0.2,0.1,0.075,0.075,0.075,0.075,1/15,1/15,1/15])
    scos=[]

    for i in range(len(datas)):
        sco=sum(feas[:,i]/max_feas*weights)
        scos.append(sco)
    return scos


def calc5_du(names,datas):
    #指标体系5，杜邦分析率
    rates=[data[names.index('杜邦分析')] for data in datas]
    return rates


if __name__=='__main__':
    file='crawl_eastmoney.csv'
    names,datas=load_data(file)
    dataArr=np.array(datas)

    class1,score1=calc1_Zscore(names,dataArr)
    score2=calc2_bathory(names,datas)
    class3,score3=calc3_Fscore(names,dataArr)
    score4=calc4_wall(names,dataArr)
    score5=calc5_du(names,datas)
    # print(class1);print(class2);print(class3);print(class4);print(class5)

    scores=[score1[i]+score2[i]+score3[i]+score4[i]+score5[i] for i in range(len(datas))]
    ret_scores=[float('%.2f' % s) for s in scores]
    # print(scores);print(np.max(scores),np.min(scores))
    # sort_scores=scores;sort_scores.sort();print(sort_scores)
    # print(sort_scores[100], sort_scores[200], sort_scores[300], sort_scores[400])
    # print(len([s for s in scores if s<5]),len([s for s in scores if s<10 and s>5]),len([s for s in scores if s>=10]))

    # maxS=np.max(scores)
    # minS=np.min(scores)
    # diffS=maxS-minS
    # ret_scores=[100*((s-minS)/diffS) for s in scores]

    ret_class=[]
    for i in range(len(ret_scores)):
        if ret_scores[i]<5:
            ret_class.append(0)
        elif ret_scores[i]<10:

            ret_class.append(1)
        else:
            ret_class.append(2)

    # print('features:',datas,'\nclasses:', ret_class,'\nscores:',ret_scores)
    # print('健康：',(class1.count('健康'),class3.count('健康')),ret_class.count('健康'))
    # print('可疑：',(class1.count('可疑'),class3.count('可疑')),ret_class.count('可疑'))
    # print('危险：',(class1.count('危险'),class3.count('危险')),ret_class.count('危险'))
    print(ret_class.count(0),ret_class.count(1),ret_class.count(2))

    '''
    五个分类
    '''
    # dataStr=[[str(x) for x in data] for data in datas]
    # fw=open('data.txt','w',encoding='utf-8')
    # fw.writelines([' '.join(names),' ','评估分数',' ','评估类别'])
    # fa=open('data.txt','a',encoding='utf-8')
    # for i in range(len(datas)):
    #     fa.writelines(['\n',' '.join(dataStr[i]),' ', str(ret_scores[i]), ' ', ret_class[i]])

    '''
    只要F分数
    '''
    # ret_class=class3
    # ret_scores=score3
    # print(ret_class);print(scores)
    # dataStr=[[str(x) for x in data] for data in datas]
    # fw=open('dataF.txt','w',encoding='utf-8')
    # fw.writelines([' '.join(names),' ','评估分数',' ','评估类别'])
    # fa=open('dataF.txt','a',encoding='utf-8')
    # for i in range(len(datas)):
    #     fa.writelines(['\n',' '.join(dataStr[i]),' ', str(ret_scores[i]), ' ', ret_class[i]])


























