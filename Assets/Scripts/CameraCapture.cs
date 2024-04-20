using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using LSL;
using static LSL.liblsl;

public class RSVPController : MonoBehaviour
{
    public Camera vrCamera;
    public LayerMask targetLayer;
    public GameObject robotLabel;
    public GameObject flickeringTarget;

    private RaycastHit hit;
    private GameObject currentTarget;
    private bool isTargetDetected = false;

    private StreamInlet eegInlet;
    private float[] eegSample;
    private double[] timestamps;
    private bool isEEGSignalDetected = false;

    private void Start()
    {
        // Set up LSL inlet for EEG data
        var info = LSL.liblsl.resolve_stream("type=EEG")[0];
        eegInlet = new StreamInlet(info);
        eegSample = new float[info.channel_count()];
        timestamps = new double[1];
    }

    private void Update()
    {
        // Cast a ray from the center of the VR camera
        if (Physics.Raycast(vrCamera.transform.position, vrCamera.transform.forward, out hit, Mathf.Infinity, targetLayer))
        {
            // Check if the hit object is a target
            if (hit.transform.gameObject.CompareTag("Target"))
            {
                // Detected a target
                isTargetDetected = true;
                currentTarget = hit.transform.gameObject;

                // Instantiate the robot label at the target's position
                Instantiate(robotLabel, currentTarget.transform.position, Quaternion.identity);

                // Check for EEG signal changes
                CheckEEGSignal();

                // If EEG signal is detected and the target has the "Robot" tag, destroy the target
                if (isEEGSignalDetected && currentTarget.CompareTag("Robot"))
                {
                    Destroy(currentTarget);
                }
            }
            else
            {
                // No target detected
                isTargetDetected = false;
                currentTarget = null;
            }
        }
        else
        {
            // No object hit, reset the target detection
            isTargetDetected = false;
            currentTarget = null;
        }
    }

    private void CheckEEGSignal()
    {
        // Pull the latest EEG sample from the inlet
        int available = (int)eegInlet.pull_sample(eegSample, 1.0);
        if (available > 0)
        {
            // Analyze the EEG sample and detect any significant changes
            if (IsEEGSignalDetected(eegSample))
            {
                isEEGSignalDetected = true;
            }
            else
            {
                isEEGSignalDetected = false;
            }
        }
    }

    private bool IsEEGSignalDetected(float[] eegSample)
    {
        // Implement your EEG signal detection logic here
        // This is a placeholder, you'll need to replace it with your actual detection algorithm
        float threshold = 0.5f;
        float maxValue = Mathf.Max(eegSample);
        return maxValue > threshold;
    }
}
