import boto3, datetime, argparse
from termcolor import colored


def get_metrics_elb(asset):
    client1 = boto3.client('elb')
    response1 = client1.describe_instance_health(
        LoadBalancerName=asset,
    )

    for instancestates in response1['InstanceStates']:
        if instancestates['State'] == 'InService':
            ins_state = colored(instancestates['State'],'green')
        else:
            ins_state = colored(instancestates['State'],'red')
        print("Instance Id: {0} | Instance State: {1} ".format(instancestates['InstanceId'], ins_state))

def get_metrics_ec2(asset):
    client = boto3.client('cloudwatch')
    response = client.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='CPUUtilization',
        StartTime=datetime.datetime.utcnow()-datetime.timedelta(seconds=7200),
        EndTime=datetime.datetime.utcnow(),
        Period=300,
        Dimensions=[
            {
                'Name': 'InstanceId',
                'Value': asset
            },
        ],
        Statistics=['Average'],
        Unit='Percent'
    )
    if len(response['Datapoints']) > 0:
        return response['Datapoints'][-1]['Average']


def asg(ASG):
    client = boto3.client('autoscaling')
    response = client.describe_auto_scaling_groups(AutoScalingGroupNames=ASG.split(','))
    ASGs = response['AutoScalingGroups']

    healthy = 0
    unhealthy = 0
    for ASG in ASGs:
        print('#'*150)
        print(colored(ASG['AutoScalingGroupName'],'red'))
        print('ASG Min Size: ', ASG['MinSize'])
        print('ASG Max Size: ', ASG['MaxSize'])
        print('ASG Desired Size: ', ASG['DesiredCapacity'])
        print('ASG instance count: ', len(ASG['Instances']))
        print('#'*150)

        for instance in ASG['Instances']:
            if instance['HealthStatus'] == 'Healthy':
                ins_health = colored('Healthy', 'green')
                ins_cpu = get_metrics_ec2(instance['InstanceId'])
                if ins_cpu and ins_cpu > 5:
                    ins_cpu = colored(ins_cpu, 'red')
                else:
                    ins_cpu = colored(ins_cpu, 'green')
                healthy += 1
            else:
                ins_health = colored(instance['HealthStatus'], 'red')
                unhealthy += 1
            if instance['LifecycleState'] == 'InService':
                ins_life = colored(instance['LifecycleState'], 'green')
            else:
                ins_life = colored(instance['LifecycleState'], 'red')
            print("Instance Id: {0} | Instance Zone: {1} | Instance LifecycleState: {2} | Instance Status: {3} | Instance Cpu: {4}".format(colored(instance['InstanceId'],'yellow'), colored(instance['AvailabilityZone'],'yellow'), ins_life, ins_health, ins_cpu))

        print('#'*150)
        print("ASG Healthy Instance Count: {0}".format(colored(healthy, 'green')))
        print("ASG Unhealthy Instance Count: {0}".format(colored(unhealthy, "red")))

        for ELB in (ASG['LoadBalancerNames']):
            print('#'*150)
            print('ELB Name: ', ELB)
            print('#'*150)
            get_metrics_elb(ELB)
            print('#'*150)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("asg",help="Enter list of autoscaling groups")
    args = parser.parse_args()
    try:
        asg(args.asg)
    except Exception as err:
        print(err)

